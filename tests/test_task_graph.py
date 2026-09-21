from __future__ import annotations

import unittest
from task_graph import TaskGraph, TaskGraphNode, TaskGraphEdge, EdgeType
from decision_trace import DecisionTrace, TracePhase
from executor import Executor, TaskType, Strategy


class TestTaskGraph(unittest.TestCase):
    def test_task_graph_structure_and_edges(self):
        graph = TaskGraph()
        n1 = graph.add_node("task_1", node_type="task", label="Main Task")
        n2 = graph.add_node("task_2", node_type="task", label="Sub Task")

        # Add parent-child edges
        graph.add_edge("task_1", "task_2", EdgeType.CHILD)
        graph.add_edge("task_2", "task_1", EdgeType.PARENT)

        # Add evidence, decision, outcome, learned_from nodes
        ev = graph.add_node("ev_1", node_type="evidence", label="Web Search Result")
        graph.add_edge("task_1", ev.id, EdgeType.EVIDENCE)

        dec = graph.add_node("dec_1", node_type="decision", label="Routed to Local Model")
        graph.add_edge("task_1", dec.id, EdgeType.DECISION)

        out = graph.add_node("out_1", node_type="outcome", label="Task Done")
        graph.add_edge("task_1", out.id, EdgeType.OUTCOME)

        learn = graph.add_node("learn_1", node_type="learned_from", label="Feedback Reflection")
        graph.add_edge("task_1", learn.id, EdgeType.LEARNED_FROM)

        self.assertEqual(graph.get_children("task_1"), ["task_2"])
        self.assertEqual(graph.get_parents("task_2"), ["task_1"])
        self.assertEqual(graph.get_evidence("task_1"), ["ev_1"])
        self.assertEqual(graph.get_decisions("task_1"), ["dec_1"])
        self.assertEqual(graph.get_outcomes("task_1"), ["out_1"])
        self.assertEqual(graph.get_learned_from("task_1"), ["learn_1"])

        causal = graph.build_causal_chain("task_1")
        self.assertEqual(len(causal["children"]), 1)
        self.assertEqual(len(causal["evidence"]), 1)
        self.assertEqual(len(causal["decisions"]), 1)
        self.assertEqual(len(causal["outcomes"]), 1)
        self.assertEqual(len(causal["learned_from"]), 1)

    def test_task_graph_serialization(self):
        graph = TaskGraph()
        graph.add_node("t1", "task", "Task 1")
        graph.add_node("t2", "task", "Task 2")
        graph.add_edge("t1", "t2", EdgeType.DEPENDENCY)

        data = graph.to_dict()
        reconstructed = TaskGraph.from_dict(data)

        self.assertIn("t1", reconstructed.nodes)
        self.assertIn("t2", reconstructed.nodes)
        self.assertEqual(reconstructed.get_dependencies("t1"), ["t2"])

    def test_executor_task_graph_integration(self):
        executor = Executor()
        parent = executor.create_task(TaskType.CHAT, "Parent prompt", "Parent Task")
        sub = executor.create_task(TaskType.CHAT, "Sub prompt", "Sub Task", parent_id=parent.id)

        self.assertIsNotNone(parent.task_graph)
        self.assertIs(parent.task_graph, sub.task_graph)

        self.assertIn(sub.id, parent.task_graph.get_children(parent.id))
        self.assertIn(parent.id, sub.task_graph.get_parents(sub.id))

        task_dict = parent.to_dict()
        self.assertIn("task_graph", task_dict)
        self.assertIn("nodes", task_dict["task_graph"])

    def test_decision_trace_sync_to_task_graph(self):
        trace = DecisionTrace()
        graph = TaskGraph()
        trace.task_graph = graph

        trace.add(TracePhase.GOVERNANCE, "gate_check", {"task_id": "root_task", "allowed": True})
        trace.add(TracePhase.RETRIEVAL, "context_fetched", {"task_id": "root_task", "facts_count": 3})
        trace.add(TracePhase.EXECUTION, "model_called", {"task_id": "root_task", "ok": True})
        trace.add(TracePhase.LEARNING, "reflected", {"task_id": "root_task", "lesson": "be concise"})

        self.assertEqual(len(graph.get_decisions("root_task")), 1)
        self.assertEqual(len(graph.get_evidence("root_task")), 1)
        self.assertEqual(len(graph.get_outcomes("root_task")), 1)
        self.assertEqual(len(graph.get_learned_from("root_task")), 1)

        portable = trace.to_portable_export(request_id="root_task")
        self.assertIn("task_graph", portable)
        self.assertIsNotNone(portable["task_graph"])
        self.assertEqual(portable["schema"], "isaac.decision_trace.portable_v1_1")


if __name__ == "__main__":
    unittest.main()
