from __future__ import annotations

import unittest

from isaac_learning_causality import (
    LEARNING_SCHEMA,
    build_learning_record,
    validate_learning_record,
)


def valid_record(**overrides):
    values = {
        "learning_id": "learn-1",
        "research_id": "research-1",
        "goal_id": "goal-1",
        "subgoal_id": "sub-1",
        "source_cycle_id": "cycle-1",
        "pre_state": {"score": 0.4},
        "research_evidence": ["evidence-1"],
        "post_state": {"score": 0.8},
        "measurable_delta": {"score_delta": 0.4},
        "affected_decision_ids": ["decision-1"],
        "evidence_event_ids": ["event-1", "event-2"],
    }
    values.update(overrides)
    return build_learning_record(**values)


class TestIsaacLearningCausality(unittest.TestCase):
    def test_valid_record_proves_before_after_and_downstream_effect(self):
        result = validate_learning_record(valid_record())
        self.assertTrue(result["valid"])
        self.assertEqual(result["schema"], LEARNING_SCHEMA)

    def test_rejects_learning_without_causal_evidence(self):
        result = validate_learning_record(valid_record(
            research_evidence=[],
            measurable_delta={},
            affected_decision_ids=[],
            evidence_event_ids=[],
        ))
        self.assertFalse(result["valid"])
        self.assertIn("missing_research_evidence", result["errors"])
        self.assertIn("missing_downstream_effect", result["errors"])
        self.assertIn("missing_measurable_delta", result["errors"])
        self.assertIn("missing_evidence_event_ids", result["errors"])

    def test_rejects_wrong_schema(self):
        data = valid_record().to_dict()
        data["schema"] = "isaac.autonomy.learning.invalid"
        result = validate_learning_record(data)
        self.assertFalse(result["valid"])
        self.assertIn("invalid_schema", result["errors"])

    def test_rejects_missing_pre_or_post_state(self):
        result = validate_learning_record(valid_record(pre_state={}, post_state={}))
        self.assertFalse(result["valid"])
        self.assertIn("pre_state", result["missing"])
        self.assertIn("post_state", result["missing"])

    def test_rejects_empty_identity_and_binding_fields(self):
        result = validate_learning_record(valid_record(
            learning_id="",
            research_id="",
            goal_id="",
            subgoal_id="",
            source_cycle_id="",
        ))
        self.assertFalse(result["valid"])
        self.assertEqual(
            set(result["missing"]),
            {"learning_id", "research_id", "goal_id", "subgoal_id", "source_cycle_id"},
        )

    def test_control_metadata_is_preserved(self):
        record = valid_record(control={"enabled": True, "arm": "learning_disabled"})
        self.assertEqual(record.to_dict()["control"]["arm"], "learning_disabled")


if __name__ == "__main__":
    unittest.main()
