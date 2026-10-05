from __future__ import annotations

import unittest

from isaac_causal import (
    CausalEdgeType,
    CausalNodeType,
    build_sequence_graph,
    normalize_audit_events,
    normalize_trace_entries,
)


class TestIsaac20CausalSchema(unittest.TestCase):
    def test_audit_normalization_preserves_evidence(self):
        events = normalize_audit_events([
            {
                "typ": "capability",
                "ms": 1234,
                "task_id": "t1",
                "allowed": False,
                "resource": "filesystem:/workspace",
            },
        ])
        self.assertEqual(events[0].node_type, CausalNodeType.POLICY_DECISION)
        self.assertFalse(events[0].data["allowed"])
        self.assertEqual(events[0].timestamp_ms, 1234)

    def test_trace_normalization_maps_known_event(self):
        events = normalize_trace_entries([
            {
                "sequence": 1,
                "ts": 2.5,
                "phase": "governance",
                "event": "capability_decision",
                "data": {"allowed": True},
            },
        ], task_id="t2")
        self.assertEqual(events[0].event_id, "trace-t2-1")
        self.assertEqual(events[0].node_type, CausalNodeType.POLICY_DECISION)
        self.assertEqual(events[0].timestamp_ms, 2500)

    def test_sequence_graph_is_explicitly_observational(self):
        events = normalize_audit_events([
            {"typ": "task", "ms": 1000, "task_id": "t1", "status": "created"},
            {"typ": "action", "ms": 1100, "task_id": "t1", "aktion": "tool_used"},
            {"typ": "error", "ms": 1200, "task_id": "t1", "fehler": "boom"},
        ])
        graph = build_sequence_graph(events)
        self.assertEqual(len(graph.events), 3)
        self.assertEqual(len(graph.edges), 2)
        self.assertTrue(all(
            e.edge_type == CausalEdgeType.OBSERVED for e in graph.edges
        ))
        self.assertTrue(all(
            e.evidence == "temporal_sequence" for e in graph.edges
        ))

    def test_events_from_different_tasks_are_not_linked(self):
        events = normalize_audit_events([
            {"typ": "action", "ms": 1000, "task_id": "a"},
            {"typ": "action", "ms": 1100, "task_id": "b"},
        ])
        self.assertEqual(build_sequence_graph(events).edges, ())


if __name__ == "__main__":
    unittest.main()
