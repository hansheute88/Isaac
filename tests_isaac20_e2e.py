from __future__ import annotations

import unittest

from audit import AuditLog
from isaac_capabilities import CapabilityRequest, RWXPolicy, RWXRegistry, evaluate_with_audit
from isaac_causal import build_causal_graph, normalize_audit_events, normalize_trace_entries
from isaac_causal_query import root_cause_candidates
from isaac_guardrails import evaluate_failure, verification_result


class TestIsaac20EndToEnd(unittest.TestCase):
    def test_authorize_execute_fail_recover_verify_chain(self):
        registry = RWXRegistry()
        registry.set_policy(
            RWXPolicy("filesystem:/workspace", write=True, source="e2e", version=1)
        )
        decision = evaluate_with_audit(
            registry,
            CapabilityRequest(
                "filesystem:/workspace",
                "write",
                principal="isaac-task",
                reason="e2e write",
                task_id="e2e-1",
            ),
        )
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.audit_event_id)

        audit_records = [
            {
                "event_id": decision.audit_event_id,
                "typ": "capability",
                "ms": 1000,
                "task_id": "e2e-1",
                **decision.as_dict(),
            },
            {
                "event_id": "action-1",
                "typ": "action",
                "ms": 1100,
                "task_id": "e2e-1",
                "authorized_by_event_id": decision.audit_event_id,
            },
            {
                "event_id": "error-1",
                "typ": "error",
                "ms": 1200,
                "task_id": "e2e-1",
                "caused_by_event_id": "action-1",
            },
            {
                "event_id": "recovery-1",
                "typ": "action",
                "ms": 1300,
                "task_id": "e2e-1",
                "triggered_by_event_id": "error-1",
            },
            {
                "event_id": "verification-1",
                "typ": "action",
                "ms": 1400,
                "task_id": "e2e-1",
                "verified_by_event_id": "recovery-1",
            },
        ]
        audit_events = normalize_audit_events(audit_records)

        trace_events = normalize_trace_entries(
            [
                {
                    "event_id": "trace-cap",
                    "sequence": 1,
                    "ts": 1.0,
                    "event": "capability_decision",
                    "data": {"audit_event_id": decision.audit_event_id, "allowed": True},
                },
                {
                    "event_id": "trace-action",
                    "sequence": 2,
                    "ts": 1.1,
                    "event": "execution_started",
                    "data": {"authorized_by_event_id": "trace-cap"},
                },
                {
                    "event_id": "trace-error",
                    "sequence": 3,
                    "ts": 1.2,
                    "event": "execution_failed",
                    "data": {"caused_by_event_id": "trace-action"},
                },
            ],
            task_id="e2e-1",
        )

        graph = build_causal_graph(audit_events + trace_events)
        self.assertTrue(any(
            edge.edge_type.value == "authorized_by"
            and edge.target_event_id == "action-1"
            for edge in graph.edges
        ))
        candidates = root_cause_candidates(graph, "error-1")
        self.assertEqual(candidates[0].event_id, "action-1")

        guardrail = evaluate_failure(
            failed_event_id="error-1",
            error="simulated failure",
            safety_critical=False,
        )
        self.assertEqual(guardrail.source_event_id, "error-1")
        verification = verification_result(
            intervention_event_id="recovery-1",
            verified=True,
            reason="e2e verification",
        )
        self.assertEqual(verification.state.value, "verified")


if __name__ == "__main__":
    unittest.main()
