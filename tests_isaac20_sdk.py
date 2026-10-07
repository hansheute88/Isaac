"""Tests for the Isaac 2.0 stable SDK facade."""
from __future__ import annotations

import unittest

from isaac_capabilities import Capability
from isaac_causal import CausalEdgeType, CausalEvent, CausalNodeType
from isaac_sdk import AgentResult, AgentRuntime


class IsaacSdkTests(unittest.TestCase):
    def setUp(self):
        self.runtime = AgentRuntime(audit=True, causal_memory=True, watchdog=True)

    def test_runtime_exposes_stable_configuration(self):
        self.assertEqual(self.runtime.SDK_VERSION, "0.1")
        self.assertTrue(self.runtime.audit_enabled)
        self.assertTrue(self.runtime.causal_memory_enabled)
        self.assertTrue(self.runtime.watchdog_enabled)
        self.assertTrue(hasattr(self.runtime, "policy"))

    def test_policy_allow_and_check_are_deterministic(self):
        self.runtime.policy.allow(
            resource="filesystem:/workspace",
            read=True,
            write=True,
            execute=False,
        )
        allowed = self.runtime.policy.check(
            resource="filesystem:/workspace",
            capability=Capability.WRITE,
            task_id="task-1",
        )
        denied = self.runtime.policy.check(
            resource="filesystem:/workspace",
            capability=Capability.EXECUTE,
            task_id="task-1",
        )
        self.assertTrue(allowed.allowed)
        self.assertFalse(denied.allowed)
        self.assertTrue(allowed.audit_event_id)
        self.assertTrue(denied.audit_event_id)

    def test_run_returns_stable_result_envelope_without_bypassing_executor(self):
        result = self.runtime.run("example-task", task_id="task-1")
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.ok)
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.output, "example-task")
        self.assertFalse(self.runtime.run(None).ok)

    def test_trace_and_root_cause_use_recorded_events(self):
        events = [
            CausalEvent(
                event_id="policy-1",
                task_id="task-1",
                node_type=CausalNodeType.POLICY_DECISION,
                timestamp_ms=1,
                source="decision_trace",
                event="capability_decision",
            ),
            CausalEvent(
                event_id="error-1",
                task_id="task-1",
                node_type=CausalNodeType.ERROR,
                timestamp_ms=2,
                source="decision_trace",
                event="execution_failed",
                data={"caused_by_event_id": "policy-1"},
            ),
        ]
        trace = self.runtime.trace(events, target_event_id="error-1")
        self.assertEqual(trace["schema"], "isaac.causal_trace.v1")
        self.assertEqual(trace["root_cause"]["candidate_count"], 1)
        self.assertEqual(
            trace["root_cause"]["candidates"][0]["confidence"],
            "explicit",
        )

    def test_root_cause_does_not_promote_observation_to_cause(self):
        events = [
            CausalEvent(
                event_id="a",
                task_id="task-1",
                node_type=CausalNodeType.OBSERVATION,
                timestamp_ms=1,
                source="audit",
                event="observation",
            ),
            CausalEvent(
                event_id="b",
                task_id="task-1",
                node_type=CausalNodeType.ERROR,
                timestamp_ms=2,
                source="audit",
                event="error",
            ),
        ]
        report = self.runtime.root_cause(events, target_event_id="b")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["candidates"][0]["confidence"], "observed")


if __name__ == "__main__":
    unittest.main()
