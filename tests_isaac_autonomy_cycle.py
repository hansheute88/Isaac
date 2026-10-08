from __future__ import annotations

import unittest

from decision_trace import DecisionTrace
from isaac_autonomy_cycle import (
    begin_cycle,
    record_authorization,
    record_evaluation,
    record_execution,
    record_learning,
    validate_cycle,
)


class TestIsaacAutonomyCycle(unittest.TestCase):
    def test_cycle_is_reconstructable_without_new_authority(self):
        trace = DecisionTrace()
        cycle = begin_cycle(
            trace,
            goal_id="goal-1",
            subgoal_id="subgoal-1",
            intent="research a bounded question",
        )
        record_authorization(
            trace, cycle, authorization_event_id="auth-1", allowed=True
        )
        record_execution(trace, cycle, execution_event_id="exec-1")
        record_evaluation(
            trace, cycle, evaluation_event_id="eval-1", outcome="success"
        )
        record_learning(trace, cycle, learning_id="learn-1")

        result = validate_cycle(cycle)
        self.assertTrue(result["valid"])
        self.assertTrue(result["authorization_observed"])
        self.assertTrue(result["execution_observed"])
        self.assertTrue(result["evaluation_observed"])
        self.assertTrue(result["learning_observed"])

        events = trace.to_list()
        self.assertEqual(events[0]["event"], "autonomy_cycle_started")
        self.assertTrue(all(e["data"]["cycle_id"] == cycle.cycle_id for e in events))

    def test_empty_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            begin_cycle(DecisionTrace(), intent="")


if __name__ == "__main__":
    unittest.main()
