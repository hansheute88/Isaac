"""Reconstruct autonomous-cycle links from an existing DecisionTrace."""
from __future__ import annotations

from typing import Any

from decision_trace import DecisionTrace
from isaac_autonomy_cycle import AutonomyCycle, validate_cycle


def reconstruct_cycle(trace: DecisionTrace, cycle_id: str) -> dict[str, Any]:
    target = str(cycle_id or "").strip()
    if not target:
        return {"ok": False, "reason": "missing_cycle_id"}

    entries = [
        e for e in trace.to_list()
        if str((e.get("data") or {}).get("cycle_id") or "") == target
    ]
    cycle = AutonomyCycle(cycle_id=target)

    for entry in entries:
        phase = str(entry.get("phase") or "")
        event_id = str(entry.get("event_id") or "")
        data = entry.get("data") or {}

        if data.get("intent") and not cycle.intent:
            cycle.intent = str(data["intent"])
        if data.get("goal_id") and not cycle.goal_id:
            cycle.goal_id = str(data["goal_id"])
        if data.get("subgoal_id") and not cycle.subgoal_id:
            cycle.subgoal_id = str(data["subgoal_id"])
        if data.get("next_cycle_id") and not cycle.next_cycle_id:
            cycle.next_cycle_id = str(data["next_cycle_id"])

        if phase == "governance" and data.get("authorization_event_id"):
            cycle.authorization_event_id = str(data["authorization_event_id"])
        elif phase == "execution" and not cycle.execution_event_id:
            cycle.execution_event_id = event_id
        elif phase == "evaluation" and not cycle.evaluation_event_id:
            cycle.evaluation_event_id = event_id
        elif phase == "learning" and not cycle.learning_id:
            cycle.learning_id = str(data.get("learning_id") or event_id)

    result = validate_cycle(cycle)
    result["related_trace_entries"] = len(entries)
    result["cycle"] = cycle.as_dict()
    return result
