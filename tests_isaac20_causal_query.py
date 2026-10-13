from __future__ import annotations

import unittest

from isaac_causal import normalize_audit_events
from isaac_causal_query import (
    CausalConfidence,
    build_root_cause_report,
    predecessors,
    root_cause_candidates,
)
from isaac_guardrails import (
    GuardrailState,
    InterventionType,
    evaluate_failure,
    verification_result,
)


class TestIsaac20CausalQuery(unittest.TestCase):
    def test_explicit_authorization_beats_temporal_observation(self):
        events = normalize_audit_events([
            {"event_id": "cap", "typ": "capability", "ms": 1000, "task_id": "t1", "allowed": True},
            {"event_id": "action", "typ": "action", "ms": 1100, "task_id": "t1",
             "authorized_by_event_id": "cap"},
            {"event_id": "err", "typ": "error", "ms": 1200, "task_id": "t1",
             "caused_by_event_id": "action"},
        ])
        graph = __import__("isaac_causal").build_causal_graph(events)
        candidates = root_cause_candidates(graph, "err")
        self.assertEqual(candidates[0].event_id, "action")
        self.assertEqual(candidates[0].confidence, CausalConfidence.EXPLICIT)

    def test_predecessors_are_queryable(self):
        events = normalize_audit_events([
            {"event_id": "a", "typ": "action", "ms": 1000, "task_id": "t1"},
            {"event_id": "b", "typ": "error", "ms": 1100, "task_id": "t1",
             "caused_by_event_id": "a"},
        ])
        graph = __import__("isaac_causal").build_causal_graph(events)
        self.assertEqual([e.event_id for e in predecessors(graph, "b")], ["a"])

    def test_root_cause_report_never_calls_observation_proven(self):
        events = normalize_audit_events([
            {"event_id": "a", "typ": "action", "ms": 1000, "task_id": "t1"},
            {"event_id": "b", "typ": "error", "ms": 1100, "task_id": "t1"},
        ])
        report = build_root_cause_report(events, "b")
        self.assertEqual(report["candidates"][0]["confidence"], "observed")
        self.assertEqual(report["verified"], [])

    def test_guardrail_quarantines_safety_critical_failure(self):
        decision = evaluate_failure(failed_event_id="err", error="unsafe", safety_critical=True)
        self.assertEqual(decision.state, GuardrailState.QUARANTINED)
        self.assertEqual(decision.intervention, InterventionType.QUARANTINE)
        self.assertTrue(decision.requires_verification)

    def test_guardrail_verification_is_explicit(self):
        result = verification_result(intervention_event_id="recover", verified=True)
        self.assertEqual(result.state, GuardrailState.VERIFIED)
        self.assertFalse(result.requires_verification)


if __name__ == "__main__":
    unittest.main()
