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
    # Correlate subsequent real DecisionTrace entries with this cycle. This adds
    # metadata only; it does not change the executor or authorization decisions.
    trace.autonomy_cycle_id = cycle.cycle_id
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



def finalize_cycle_from_task(task: Any) -> dict[str, Any]:
    """Link observed executor evidence to the cycle without making governance decisions.

    Only real trace entries are accepted as evidence. Missing authorization,
    execution, evaluation, or learning remains missing rather than being inferred.
    """
    context = getattr(task, "retrieved_context", None) or {}
    if not isinstance(context, dict):
        return {"ok": False, "reason": "missing_task_context"}
    cycle_id = str(context.get("autonomy_cycle_id") or "").strip()
    goal_id = str(context.get("goal_id") or "").strip()
    subgoal_id = str(context.get("subgoal_id") or "").strip()
    if not cycle_id:
        return {"ok": False, "reason": "missing_cycle_id"}
    trace = getattr(task, "decision_trace", None)
    if trace is None or not hasattr(trace, "entries"):
        return {"ok": False, "reason": "missing_decision_trace"}

    cycle = AutonomyCycle(cycle_id=cycle_id, goal_id=goal_id, subgoal_id=subgoal_id,
                          intent=str(getattr(task, "prompt", "") or "")[:1000])
    entries = list(trace.entries)
    def event_data(entry: Any) -> dict[str, Any]:
        return dict(getattr(entry, "data", {}) or {})
    def event_name(entry: Any) -> str:
        return str(getattr(entry, "event", "") or "")
    def event_id(entry: Any) -> str:
        return str(getattr(entry, "event_id", "") or "")

    # Prefer action-level authorization when a tool/action was proposed. If no
    # action was attempted, the active-goal scope authorization is still real
    # evidence that the background task was allowed to pursue its owner goal.
    action_auths = [e for e in entries if event_name(e) in {
        "capability_decision", "tool_execution_capability", "tool_authorization_decision"
    }]
    successful_executions = [e for e in entries if (
        event_name(e) == "execution_succeeded"
        or (event_name(e) == "model_call" and event_data(e).get("ok") is True)
        or (event_name(e) == "quality_scored" and event_data(e).get("via") == "search")
    )]
    auth = None
    if action_auths:
        # When execution succeeded, tie authorization to the same selected tool.
        last_success = successful_executions[-1] if successful_executions else None
        success_identifier = str(event_data(last_success).get("identifier") or "") if last_success else ""
        matching = [e for e in action_auths if (
            not success_identifier
            or str(event_data(e).get("tool_identifier") or event_data(e).get("identifier") or "") == success_identifier
        )]
        auth = matching[-1] if matching else action_auths[-1]
    else:
        auth = next((e for e in reversed(entries) if event_name(e) == "goal_scope_authorization_observed"), None)

    if auth is not None:
        data = event_data(auth)
        allowed = bool(data.get("allowed", False))
        record_authorization(trace, cycle, authorization_event_id=event_id(auth), allowed=allowed)
    else:
        allowed = False

    successful_execution = successful_executions[-1] if successful_executions else None
    denied = auth is not None and not allowed
    if successful_execution is not None and allowed and not denied:
        record_execution(trace, cycle, execution_event_id=event_id(successful_execution))

    evaluation = next((e for e in reversed(entries) if event_name(e) == "quality_scored"), None)
    if evaluation is not None:
        record_evaluation(trace, cycle, evaluation_event_id=event_id(evaluation),
                          outcome="success" if bool(event_data(evaluation).get("acceptable", True)) else "unacceptable")

    learning = next((e for e in reversed(entries) if event_name(e) == "goal_learning_recorded"), None)
    if learning is not None:
        learning_data = event_data(learning)
        if learning_data.get("goal_id") == goal_id and learning_data.get("subgoal_id", "") == subgoal_id:
            record_learning(trace, cycle, learning_id=event_id(learning))

    result = validate_cycle(cycle)
    result.update({
        "ok": True,
        "task_id": str(getattr(task, "id", "") or ""),
        "goal_id": goal_id,
        "subgoal_id": subgoal_id,
        "research_id": str(getattr(task, "id", "") or "") if str(getattr(getattr(task, "typ", None), "value", getattr(task, "typ", ""))).lower() == "research" else "",
        "authorization_denied": denied,
        "execution_observed": bool(cycle.execution_event_id),
        "evaluation_observed": bool(cycle.evaluation_event_id),
        "learning_observed": bool(cycle.learning_id),
    })
    return result
