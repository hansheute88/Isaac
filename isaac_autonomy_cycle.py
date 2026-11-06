"""Isaac 30-Day Autonomy — reconstructable autonomous decision cycle.

This module is an evidence contract only. It does not authorize or execute
actions and therefore cannot become a second privilege authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from decision_trace import DecisionTrace, TracePhase


def _emit_evidence(event_type: str, payload: dict[str, Any]) -> None:
    # Evidence persistence is opt-in; official proof mode fails closed on write errors.
    from isaac_30day_evidence import emit_runtime_event
    emit_runtime_event(event_type, payload)


CYCLE_SCHEMA = "isaac.autonomy.cycle.v1"


@dataclass
class AutonomyCycle:
    cycle_id: str = field(default_factory=lambda: f"cycle_{uuid.uuid4().hex}")
    goal_id: str = ""
    subgoal_id: str = ""
    intent: str = ""
    authorization_event_id: str = ""
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
    _emit_evidence("autonomy_cycle_started", cycle.as_dict())
    return cycle


def record_authorization(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    authorization_event_id: str,
    allowed: bool,
) -> None:
    """Record an existing authorization decision; never make one."""
    cycle.authorization_event_id = str(authorization_event_id or "")
    trace.add(
        TracePhase.GOVERNANCE,
        "autonomy_authorization_observed",
        {
            "cycle_id": cycle.cycle_id,
            "authorization_event_id": cycle.authorization_event_id,
            "allowed": bool(allowed),
        },
    )
    _emit_evidence("autonomy_authorization_observed", {
        "cycle_id": cycle.cycle_id, "authorization_event_id": cycle.authorization_event_id,
        "allowed": bool(allowed),
    })


def record_execution(
    trace: DecisionTrace,
    cycle: AutonomyCycle,
    *,
    execution_event_id: str,
) -> None:
    cycle.execution_event_id = str(execution_event_id or "")
    trace.add(
        TracePhase.EXECUTION,
        "autonomy_execution_observed",
        {
            "cycle_id": cycle.cycle_id,
            "execution_event_id": cycle.execution_event_id,
        },
    )
    _emit_evidence("autonomy_execution_observed", {
        "cycle_id": cycle.cycle_id, "execution_event_id": cycle.execution_event_id,
    })


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
    _emit_evidence("autonomy_evaluation_recorded", {
        "cycle_id": cycle.cycle_id, "evaluation_event_id": cycle.evaluation_event_id,
        "outcome": str(outcome or ""),
    })


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
    _emit_evidence("autonomy_learning_recorded", {
        "cycle_id": cycle.cycle_id, "learning_id": cycle.learning_id,
    })


def validate_cycle(cycle: AutonomyCycle) -> dict[str, Any]:
    missing = cycle.missing_required()
    return {
        "schema": CYCLE_SCHEMA,
        "cycle_id": cycle.cycle_id,
        "valid": not missing,
        "missing_required": missing,
        "authorization_observed": bool(cycle.authorization_event_id),
        "execution_observed": bool(cycle.execution_event_id),
        "evaluation_observed": bool(cycle.evaluation_event_id),
        "learning_observed": bool(cycle.learning_id),
    }
