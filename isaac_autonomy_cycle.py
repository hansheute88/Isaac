"""Isaac 30-Day Autonomy — reconstructable autonomous decision cycle.

This module is an evidence contract only. It does not authorize or execute
actions and therefore cannot become a second privilege authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from decision_trace import DecisionTrace, TracePhase


CYCLE_SCHEMA = "isaac.autonomy.cycle.v1"


@dataclass
class AutonomyCycle:
    cycle_id: str = field(default_factory=lambda: f"cycle_{uuid.uuid4().hex}")
    goal_id: str = ""
    subgoal_id: str = ""
    intent: str = ""
    authorization_event_id: str = ""
    authorization_allowed: bool | None = None
    authorization_action_id: str = ""
    authorization_scope: str = ""
    execution_action_id: str = ""
    execution_scope: str = ""
    execution_event_id: str = ""
    evaluation_event_id: str = ""
    learning_id: str = ""
    next_cycle_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CYCLE_SCHEMA,
            "cycle_id": self.cycle_id,
            "goal_id": self.goal_id,
            "subgoal_id": self.subgoal_id,
            "intent": self.intent,
            "authorization_event_id": self.authorization_event_id,
            "authorization_allowed": self.authorization_allowed,
            "authorization_action_id": self.authorization_action_id,
            "authorization_scope": self.authorization_scope,
            "execution_action_id": self.execution_action_id,
            "execution_scope": self.execution_scope,
            "execution_event_id": self.execution_event_id,
            "evaluation_event_id": self.evaluation_event_id,
            "learning_id": self.learning_id,
            "next_cycle_id": self.next_cycle_id,
        }

    def missing_required(self) -> list[str]:
        required = ("cycle_id", "intent", "authorization_event_id")
        return [key for key in required if not str(getattr(self, key, "")).strip()]


def begin_cycle(
    trace: DecisionTrace,
    *,
    goal_id: str = "",
    subgoal_id: str = "",
    intent: str,
) -> AutonomyCycle:
    """Start an observable cycle; no authorization or execution occurs here."""
    cycle = AutonomyCycle(
        goal_id=goal_id,
        subgoal_id=subgoal_id,
        intent=(intent or "").strip(),
    )
    if not cycle.intent:
        raise ValueError("intent must not be empty")
    trace.add(
        TracePhase.GOVERNANCE,
        "autonomy_cycle_started",
        {
            "schema": CYCLE_SCHEMA,
            "cycle_id": cycle.cycle_id,
            "goal_id": cycle.goal_id,
            "subgoal_id": cycle.subgoal_id,
            "intent": cycle.intent,
        },
    )
    return cycle


def record_authorization(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    authorization_event_id: str,
    allowed: bool,
    action_id: str = "",
    scope: str = "",
) -> None:
    """Record an existing authorization decision; never make one."""
    cycle.authorization_event_id = str(authorization_event_id or "")
    cycle.authorization_allowed = allowed is True
    cycle.authorization_action_id = str(action_id or "").strip()
    cycle.authorization_scope = str(scope or "").strip()
    trace.add(
        TracePhase.GOVERNANCE,
        "autonomy_authorization_observed",
        {
            "cycle_id": cycle.cycle_id,
            "authorization_event_id": cycle.authorization_event_id,
            "allowed": allowed is True,
            "action_id": cycle.authorization_action_id,
            "scope": cycle.authorization_scope,
        },
    )


def record_execution(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    execution_event_id: str,
    action_id: str = "",
    scope: str = "",
) -> None:
    cycle.execution_event_id = str(execution_event_id or "")
    cycle.execution_action_id = str(action_id or "").strip()
    cycle.execution_scope = str(scope or "").strip()
    trace.add(
        TracePhase.EXECUTION,
        "autonomy_execution_observed",
        {
            "cycle_id": cycle.cycle_id,
            "execution_event_id": cycle.execution_event_id,
            "action_id": cycle.execution_action_id,
            "scope": cycle.execution_scope,
        },
    )


def record_evaluation(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    evaluation_event_id: str,
    outcome: str,
) -> None:
    cycle.evaluation_event_id = str(evaluation_event_id or "")
    trace.add(
        TracePhase.EVALUATION,
        "autonomy_evaluation_recorded",
        {
            "cycle_id": cycle.cycle_id,
            "evaluation_event_id": cycle.evaluation_event_id,
            "outcome": str(outcome or ""),
        },
    )


def record_learning(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    learning_id: str,
) -> None:
    cycle.learning_id = str(learning_id or "")
    trace.add(
        TracePhase.LEARNING,
        "autonomy_learning_recorded",
        {
            "cycle_id": cycle.cycle_id,
            "learning_id": cycle.learning_id,
        },
    )


def validate_cycle(cycle: AutonomyCycle) -> dict[str, Any]:
    missing = cycle.missing_required()
    binding_errors: list[str] = []
    if cycle.execution_event_id:
        if not cycle.authorization_action_id or not cycle.execution_action_id:
            binding_errors.append("authorization_action_binding_missing")
        elif cycle.authorization_action_id != cycle.execution_action_id:
            binding_errors.append("authorization_action_mismatch")
        if not cycle.authorization_scope or not cycle.execution_scope:
            binding_errors.append("authorization_scope_binding_missing")
        elif cycle.authorization_scope != cycle.execution_scope:
            binding_errors.append("authorization_scope_mismatch")
    authorization_error = (
        "authorization_missing" if not cycle.authorization_event_id
        else "authorization_not_allowed" if cycle.authorization_allowed is not True
        else binding_errors[0] if binding_errors else None
    )
    return {
        "schema": CYCLE_SCHEMA,
        "cycle_id": cycle.cycle_id,
        "valid": not missing and cycle.authorization_allowed is True and not binding_errors,
        "missing_required": missing,
        "authorization_observed": bool(cycle.authorization_event_id),
        "authorization_allowed": cycle.authorization_allowed is True,
        "authorization_error": authorization_error,
        "authorization_binding_errors": binding_errors,
        "execution_observed": bool(cycle.execution_event_id),
        "evaluation_observed": bool(cycle.evaluation_event_id),
        "learning_observed": bool(cycle.learning_id),
    }
