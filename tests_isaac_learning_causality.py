from __future__ import annotations

import unittest

from isaac_learning_causality import (
    LEARNING_SCHEMA,
    build_learning_record,
    validate_learning_record,
)


class TestIsaacLearningCausality(unittest.TestCase):
    def test_valid_record_proves_before_after_and_downstream_effect(self):
        record = build_learning_record(
            learning_id="learn-1",
            research_id="research-1",
            goal_id="goal-1",
            subgoal_id="sub-1",
            source_cycle_id="cycle-1",
            pre_state={"score": 0.4},
            research_evidence=["evidence-1"],
            post_state={"score": 0.8},
            measurable_delta={"score_delta": 0.4},
            affected_decision_ids=["decision-1"],
            evidence_event_ids=["event-1", "event-2"],
        )
        result = validate_learning_record(record)
        self.assertTrue(result["valid"])
        self.assertEqual(result["schema"], LEARNING_SCHEMA)

    def test_rejects_learning_without_causal_evidence(self):
        record = build_learning_record(
            learning_id="learn-2",
            research_id="research-2",
            goal_id="goal-1",
            subgoal_id="sub-1",
            source_cycle_id="cycle-1",
            pre_state={"score": 0.4},
            research_evidence=[],
            post_state={"score": 0.8},
            measurable_delta={},
            affected_decision_ids=[],
            evidence_event_ids=[],
        )
        result = validate_learning_record(record)
        self.assertFalse(result["valid"])
        self.assertIn("missing_research_evidence", result["errors"])
        self.assertIn("missing_downstream_effect", result["errors"])
        self.assertIn("missing_measurable_delta", result["errors"])


if __name__ == "__main__":
    unittest.main()
