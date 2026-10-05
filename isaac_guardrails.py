"""Isaac 2.0 cybernetic guardrail primitives.

This module is deliberately additive. It does not replace privilege,
constitution, sudo, tool policy, or R/W/X authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from audit import AuditLog


class GuardrailState(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    QUARANTINED = "quarantined"
    RECOVERING = "recovering"
    VERIFIED = "verified"
    FAILED = "failed"


class InterventionType(str, Enum):
    OBSERVE = "observe"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    RECOVER = "recover"
    VERIFY = "verify"


@dataclass(frozen=True)
class GuardrailDecision:
    state: GuardrailState
    intervention: InterventionType
    reason: str
    source_event_id: str = ""
    requires_verification: bool = True

    def as_dict(self) -> dict:
        return {
            "state": self.state.value,
            "intervention": self.intervention.value,
            "reason": self.reason,
            "source_event_id": self.source_event_id,
            "requires_verification": self.requires_verification,
        }


def evaluate_failure(
    *,
    failed_event_id: str,
    error: str,
    safety_critical: bool = False,
) -> GuardrailDecision:
    """Choose a conservative intervention; never auto-escalate privileges."""
    if safety_critical:
        return GuardrailDecision(
            GuardrailState.QUARANTINED,
            InterventionType.QUARANTINE,
            "safety_critical_failure",
            failed_event_id,
            True,
        )
    return GuardrailDecision(
        GuardrailState.DEGRADED,
        InterventionType.RECOVER,
        (error or "runtime_failure")[:200],
        failed_event_id,
        True,
    )


def verification_result(
    *,
    intervention_event_id: str,
    verified: bool,
    reason: str = "",
) -> GuardrailDecision:
    return GuardrailDecision(
        GuardrailState.VERIFIED if verified else GuardrailState.FAILED,
        InterventionType.VERIFY,
        reason or ("verification_passed" if verified else "verification_failed"),
        intervention_event_id,
        False,
    )


class GuardrailController:
    """Runtime bridge to existing enforcement authorities.

    ProviderBlacklist remains the single provider availability authority.
    Guardrails add intervention evidence and explicit verification semantics.
    """
    def __init__(self, provider_blacklist=None):
        self._provider_blacklist = provider_blacklist
        self._states: dict[str, GuardrailState] = {}
        self._last_intervention: dict[str, str] = {}

    def _blacklist(self):
        if self._provider_blacklist is None:
            from watchdog import get_blacklist
            self._provider_blacklist = get_blacklist()
        return self._provider_blacklist

    def state(self, resource: str) -> GuardrailState:
        return self._states.get(resource, GuardrailState.NOMINAL)

    def intervene_provider(self, *, provider: str, failed_event_id: str, error: str,
                           safety_critical: bool = False, task_id: str = "") -> GuardrailDecision:
        decision = evaluate_failure(
            failed_event_id=failed_event_id, error=error,
            safety_critical=safety_critical,
        )
        resource = f"provider:{provider}"
        self._states[resource] = decision.state
        if decision.intervention is InterventionType.QUARANTINE:
            self._blacklist().quarantine(
                provider, reason=decision.reason, source_event_id=failed_event_id
            )
        entry = AuditLog.action(
            "Guardrail", decision.intervention.value,
            f"resource={resource} reason={decision.reason} task={task_id}",
            erfolg=False,
        )
        event_id = entry.get("event_id", "") if isinstance(entry, dict) else ""
        if event_id:
            self._last_intervention[resource] = event_id
        return decision

    def begin_recovery(self, *, resource: str, source_event_id: str,
                       reason: str, task_id: str = "") -> str:
        self._states[resource] = GuardrailState.RECOVERING
        entry = AuditLog.action(
            "Guardrail", InterventionType.RECOVER.value,
            f"resource={resource} source={source_event_id} reason={reason} task={task_id}",
            erfolg=True,
        )
        return entry.get("event_id", "") if isinstance(entry, dict) else ""

    def verify_provider(self, *, provider: str, intervention_event_id: str,
                        verified: bool, reason: str = "", task_id: str = "") -> GuardrailDecision:
        decision = verification_result(
            intervention_event_id=intervention_event_id,
            verified=verified, reason=reason,
        )
        resource = f"provider:{provider}"
        self._states[resource] = decision.state
        if verified:
            self._blacklist().verify_quarantine(provider)
        entry = AuditLog.action(
            "Guardrail", InterventionType.VERIFY.value,
            f"resource={resource} source={intervention_event_id} "
            f"verified={verified} reason={decision.reason} task={task_id}",
            erfolg=verified,
        )
        event_id = entry.get("event_id", "") if isinstance(entry, dict) else ""
        if event_id:
            self._last_intervention[resource] = event_id
        return decision

    def last_intervention_event_id(self, resource: str) -> str:
        return self._last_intervention.get(resource, "")

    def snapshot(self) -> dict:
        return {
            "states": {k: v.value for k, v in self._states.items()},
            "last_intervention": dict(self._last_intervention),
        }


_guardrails: Optional[GuardrailController] = None

def get_guardrail_controller() -> GuardrailController:
    global _guardrails
    if _guardrails is None:
        _guardrails = GuardrailController()
    return _guardrails
