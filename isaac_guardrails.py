"""Isaac 2.0 cybernetic guardrail primitives.

This module is deliberately additive. It does not replace privilege,
constitution, sudo, tool policy, or R/W/X authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
