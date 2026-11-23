from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LEARNING_SCHEMA = "isaac.autonomy.learning.v1"


@dataclass(frozen=True)
class LearningRecord:
    learning_id: str
    research_id: str
    goal_id: str
    subgoal_id: str
    source_cycle_id: str
    pre_state: dict[str, Any]
    research_evidence: list[str]
    post_state: dict[str, Any]
    measurable_delta: dict[str, Any]
    affected_decision_ids: list[str]
    evidence_event_ids: list[str]
    control: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LEARNING_SCHEMA,
            "learning_id": self.learning_id,
            "research_id": self.research_id,
            "goal_id": self.goal_id,
            "subgoal_id": self.subgoal_id,
            "source_cycle_id": self.source_cycle_id,
            "pre_state": self.pre_state,
            "research_evidence": self.research_evidence,
            "post_state": self.post_state,
            "measurable_delta": self.measurable_delta,
            "affected_decision_ids": self.affected_decision_ids,
            "evidence_event_ids": self.evidence_event_ids,
            "control": self.control,
        }


def validate_learning_record(record: LearningRecord | dict[str, Any]) -> dict[str, Any]:
    data = record.to_dict() if isinstance(record, LearningRecord) else record
    required = (
        "learning_id", "research_id", "goal_id", "subgoal_id",
        "source_cycle_id", "pre_state", "research_evidence", "post_state",
        "measurable_delta", "affected_decision_ids", "evidence_event_ids",
    )
    missing = [key for key in required if not data.get(key)]
    errors: list[str] = []
    if data.get("schema") != LEARNING_SCHEMA:
        errors.append("invalid_schema")
    if not isinstance(data.get("research_evidence"), list) or not data.get("research_evidence"):
        errors.append("missing_research_evidence")
    if not isinstance(data.get("evidence_event_ids"), list) or not data.get("evidence_event_ids"):
        errors.append("missing_evidence_event_ids")
    if not isinstance(data.get("affected_decision_ids"), list) or not data.get("affected_decision_ids"):
        errors.append("missing_downstream_effect")
    if not isinstance(data.get("measurable_delta"), dict) or not data.get("measurable_delta"):
        errors.append("missing_measurable_delta")
    if not isinstance(data.get("pre_state"), dict) or not isinstance(data.get("post_state"), dict):
        errors.append("invalid_state_snapshots")
    return {
        "valid": not missing and not errors,
        "missing": missing,
        "errors": errors,
        "schema": data.get("schema"),
    }


def build_learning_record(
    *,
    learning_id: str,
    research_id: str,
    goal_id: str,
    subgoal_id: str,
    source_cycle_id: str,
    pre_state: dict[str, Any],
    research_evidence: list[str],
    post_state: dict[str, Any],
    measurable_delta: dict[str, Any],
    affected_decision_ids: list[str],
    evidence_event_ids: list[str],
    control: dict[str, Any] | None = None,
) -> LearningRecord:
    record = LearningRecord(
        learning_id=learning_id,
        research_id=research_id,
        goal_id=goal_id,
        subgoal_id=subgoal_id,
        source_cycle_id=source_cycle_id,
        pre_state=pre_state,
        research_evidence=research_evidence,
        post_state=post_state,
        measurable_delta=measurable_delta,
        affected_decision_ids=affected_decision_ids,
        evidence_event_ids=evidence_event_ids,
        control=control,
    )
    validation = validate_learning_record(record)
    if validation.get("valid"):
        from isaac_30day_evidence import emit_runtime_event
        emit_runtime_event("research_cycle_completed", record.to_dict())
        emit_runtime_event("autonomy_learning_recorded", record.to_dict())
    return record
