from __future__ import annotations

import unittest

from isaac_causal import (
    CausalEdgeType,
    CausalNodeType,
    build_causal_graph,
    build_explicit_relationship_edges,
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

    def test_explicit_authorization_relationship_is_evidence_backed(self):
        events = normalize_audit_events([
            {"event_id": "decision-1", "typ": "capability", "ms": 1000, "task_id": "t1", "allowed": True},
            {"event_id": "action-1", "typ": "action", "ms": 1100, "task_id": "t1",
             "authorized_by_event_id": "decision-1", "aktion": "write"},
        ])
        edges = build_explicit_relationship_edges(events)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].source_event_id, "decision-1")
        self.assertEqual(edges[0].target_event_id, "action-1")
        self.assertEqual(edges[0].edge_type, CausalEdgeType.AUTHORIZED_BY)
        self.assertEqual(edges[0].evidence, "explicit:authorized_by_event_id")

    def test_explicit_relationship_cannot_cross_tasks(self):
        events = normalize_audit_events([
            {"event_id": "decision-a", "typ": "capability", "ms": 1000, "task_id": "a"},
            {"event_id": "action-b", "typ": "action", "ms": 1100, "task_id": "b",
             "authorized_by_event_id": "decision-a"},
        ])
        self.assertEqual(build_explicit_relationship_edges(events), ())

    def test_unknown_or_missing_reference_is_not_inferred(self):
        events = normalize_audit_events([
            {"event_id": "a", "typ": "capability", "ms": 1000, "task_id": "t1"},
            {"event_id": "b", "typ": "action", "ms": 1100, "task_id": "t1",
             "authorized_by_event_id": "does-not-exist"},
        ])
        self.assertEqual(build_explicit_relationship_edges(events), ())

    def test_combined_graph_keeps_observation_and_explicit_edges_distinct(self):
        events = normalize_audit_events([
            {"event_id": "decision-1", "typ": "capability", "ms": 1000, "task_id": "t1"},
            {"event_id": "action-1", "typ": "action", "ms": 1100, "task_id": "t1",
             "authorized_by_event_id": "decision-1"},
        ])
        graph = build_causal_graph(events)
        self.assertEqual(len(graph.events), 2)
        self.assertEqual(len(graph.edges), 2)
        self.assertEqual(
            {edge.edge_type for edge in graph.edges},
            {CausalEdgeType.OBSERVED, CausalEdgeType.AUTHORIZED_BY},
        )


if __name__ == "__main__":
    unittest.main()
