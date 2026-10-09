from __future__ import annotations

import unittest

from decision_trace import DecisionTrace, TracePhase
from isaac_autonomy_cycle import begin_cycle
from isaac_autonomy_reconstruction import reconstruct_cycle


class TestIsaacAutonomyReconstruction(unittest.TestCase):
    def test_reconstructs_only_existing_evidence(self):
        trace = DecisionTrace()
        cycle = begin_cycle(
            trace,
            goal_id="goal-1",
            subgoal_id="sub-1",
            intent="research bounded question",
        )
        trace.add(
            TracePhase.GOVERNANCE,
            "authorization_observed",
            {
                "cycle_id": cycle.cycle_id,
                "authorization_event_id": "auth-1",
            },
        )
        trace.add(
            TracePhase.EXECUTION,
            "execution_observed",
            {"cycle_id": cycle.cycle_id},
        )
        trace.add(
            TracePhase.EVALUATION,
            "evaluation_observed",
            {"cycle_id": cycle.cycle_id},
        )
        trace.add(
            TracePhase.LEARNING,
            "learning_recorded",
            {"cycle_id": cycle.cycle_id, "learning_id": "learn-1"},
        )

        result = reconstruct_cycle(trace, cycle.cycle_id)

        self.assertTrue(result["valid"])
        self.assertEqual(result["cycle"]["authorization_event_id"], "auth-1")
        self.assertTrue(result["cycle"]["execution_event_id"])
        self.assertTrue(result["cycle"]["evaluation_event_id"])
        self.assertEqual(result["cycle"]["learning_id"], "learn-1")

    def test_missing_authorization_is_not_invented(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="observe")

        result = reconstruct_cycle(trace, cycle.cycle_id)

        self.assertFalse(result["valid"])
        self.assertFalse(result["cycle"]["authorization_event_id"])


    def test_denied_or_started_actions_are_not_reconstructed_as_execution(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="try a bounded action")
        trace.add(
            TracePhase.GOVERNANCE,
            "tool_authorization_decision",
            {"allowed": False, "tool_identifier": "test-tool"},
        )
        trace.add(
            TracePhase.EXECUTION,
            "execution_started",
            {"identifier": "test-tool"},
        )
        trace.add(
            TracePhase.LEARNING,
            "procedure_record",
            {"tools": ["test-tool"]},
        )

        result = reconstruct_cycle(trace, cycle.cycle_id)

        self.assertTrue(result["cycle"]["authorization_event_id"])
        self.assertFalse(result["cycle"]["execution_event_id"])
        self.assertFalse(result["cycle"]["learning_id"])



if __name__ == "__main__":
    unittest.main()
