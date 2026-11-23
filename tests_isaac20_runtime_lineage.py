from __future__ import annotations

import unittest

from decision_trace import DecisionTrace, TracePhase
from isaac_causal import build_causal_graph, normalize_trace_entries


class TestIsaac20RuntimeLineage(unittest.TestCase):
    def test_trace_relationships_survive_normalization(self):
        trace = DecisionTrace()
        cap = trace.add(
            TracePhase.GOVERNANCE,
            "capability_decision",
            {"allowed": True, "audit_event_id": "audit-cap"},
        )
        action = trace.add(
            TracePhase.EXECUTION,
            "execution_started",
            {"authorized_by_event_id": cap.event_id},
        )
        failed = trace.add(
            TracePhase.EXECUTION,
            "execution_failed",
            {"caused_by_event_id": action.event_id},
        )
        events = normalize_trace_entries(trace.to_list(), task_id="t1")
        graph = build_causal_graph(events)
        relations = {(e.source_event_id, e.target_event_id, e.edge_type.value) for e in graph.edges}
        self.assertIn((cap.event_id, action.event_id, "authorized_by"), relations)
        self.assertIn((action.event_id, failed.event_id, "caused_by"), relations)

    def test_each_runtime_event_has_stable_id(self):
        trace = DecisionTrace()
        entry = trace.add(TracePhase.EXECUTION, "execution_succeeded", {})
        self.assertTrue(entry.event_id)
        self.assertEqual(trace.to_list()[0]["event_id"], entry.event_id)


if __name__ == "__main__":
    unittest.main()
