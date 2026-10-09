from __future__ import annotations

import unittest

from decision_trace import DecisionTrace, TracePhase
from isaac_governance_gate import validate_execution_authorization


def auth(trace, action_id, allowed):
    trace.add(TracePhase.GOVERNANCE, "authorization_decision", {
        "action_id": action_id,
        "authorization_event_id": f"auth-{action_id}-{allowed}",
        "allowed": allowed,
    })


def execute(trace, action_id):
    trace.add(TracePhase.EXECUTION, "tool_execution", {
        "action_id": action_id,
        "execution_event_id": f"exec-{action_id}",
    })


class TestIsaacGovernanceGate(unittest.TestCase):
    def test_deny_before_execution_is_rejected(self):
        trace = DecisionTrace()
        auth(trace, "a1", False)
        execute(trace, "a1")
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("denied_action_executed:a1", result["violations"])

    def test_deny_without_execution_passes(self):
        trace = DecisionTrace()
        auth(trace, "a1", False)
        result = validate_execution_authorization(trace)
        self.assertTrue(result["valid"])
        self.assertEqual(result["checked_executions"], 0)

    def test_execution_without_authorization_fails_closed(self):
        trace = DecisionTrace()
        execute(trace, "a2")
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("execution_without_authorization:a2", result["violations"])

    def test_allowed_action_can_execute(self):
        trace = DecisionTrace()
        auth(trace, "a3", True)
        execute(trace, "a3")
        result = validate_execution_authorization(trace)
        self.assertTrue(result["valid"])

    def test_deny_cannot_be_overwritten_by_later_allow(self):
        trace = DecisionTrace()
        auth(trace, "a4", False)
        auth(trace, "a4", True)
        execute(trace, "a4")
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("denied_action_executed:a4", result["violations"])

    def test_action_ids_are_correlated_independently(self):
        trace = DecisionTrace()
        auth(trace, "allowed", True)
        auth(trace, "blocked", False)
        execute(trace, "allowed")
        result = validate_execution_authorization(trace)
        self.assertTrue(result["valid"])
        self.assertEqual(result["checked_executions"], 1)

    def test_real_executor_trace_allow_correlates_with_execution_started(self):
        trace = DecisionTrace()
        trace.add(TracePhase.GOVERNANCE, "tool_execution_capability", {
            "tool_identifier": "real-tool",
            "resource": "tool:real-tool",
            "allowed": True,
        })
        trace.add(TracePhase.EXECUTION, "execution_started", {
            "identifier": "real-tool",
        })
        result = validate_execution_authorization(trace)
        self.assertTrue(result["valid"])
        self.assertEqual(result["checked_executions"], 1)

    def test_real_executor_trace_deny_blocks_execution_started(self):
        trace = DecisionTrace()
        trace.add(TracePhase.GOVERNANCE, "tool_execution_capability", {
            "tool_identifier": "real-tool",
            "resource": "tool:real-tool",
            "allowed": False,
        })
        trace.add(TracePhase.EXECUTION, "execution_started", {
            "identifier": "real-tool",
        })
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("denied_action_executed:real-tool", result["violations"])

    def test_missing_allow_metadata_fails_closed(self):
        trace = DecisionTrace()
        trace.add(TracePhase.GOVERNANCE, "tool_execution_capability", {
            "tool_identifier": "real-tool",
            "resource": "tool:real-tool",
        })
        trace.add(TracePhase.EXECUTION, "execution_started", {
            "identifier": "real-tool",
        })
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("denied_action_executed:real-tool", result["violations"])

    def test_missing_action_id_fails_closed(self):
        trace = DecisionTrace()
        trace.add(TracePhase.EXECUTION, "tool_execution", {"execution_event_id": "exec-no-id"})
        result = validate_execution_authorization(trace)
        self.assertFalse(result["valid"])
        self.assertIn("execution_missing_action_id", result["violations"])


if __name__ == "__main__":
    unittest.main()
