"""Audit authorization and execution events in a DecisionTrace.

This is an evidence validator, not an authorization engine. It fails closed
when an execution has no matching allow decision or follows any deny decision.
"""
from __future__ import annotations

from typing import Any

from decision_trace import DecisionTrace, TracePhase


def validate_execution_authorization(trace: DecisionTrace) -> dict[str, Any]:
    decisions: dict[str, list[bool]] = {}
    violations: list[str] = []
    executions: list[str] = []

    for entry in trace.entries:
        data = entry.data or {}
        action_id = str(data.get("action_id") or "").strip()
        if entry.phase == TracePhase.GOVERNANCE and entry.event == "authorization_decision":
            if not action_id:
                violations.append("authorization_missing_action_id")
                continue
            decisions.setdefault(action_id, []).append(data.get("allowed") is True)
        elif entry.phase == TracePhase.EXECUTION and entry.event == "tool_execution":
            if not action_id:
                violations.append("execution_missing_action_id")
            else:
                executions.append(action_id)

    for action_id in executions:
        history = decisions.get(action_id, [])
        if not history:
            violations.append(f"execution_without_authorization:{action_id}")
        elif False in history:
            violations.append(f"denied_action_executed:{action_id}")
        elif history[-1] is not True:
            violations.append(f"execution_without_current_allow:{action_id}")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "checked_executions": len(executions),
    }
