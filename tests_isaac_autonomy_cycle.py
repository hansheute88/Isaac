from __future__ import annotations

import unittest
from unittest.mock import patch

from decision_trace import DecisionTrace
from isaac_autonomy_cycle import (
    begin_cycle,
    record_authorization,
    record_evaluation,
    record_execution,
    record_learning,
    validate_cycle,
    finalize_cycle_from_task,
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

    def test_whitespace_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            begin_cycle(DecisionTrace(), intent="   ")

    def test_cycle_does_not_claim_authorization_or_execution_at_start(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="observe")
        result = validate_cycle(cycle)
        self.assertFalse(result["authorization_observed"])
        self.assertFalse(result["execution_observed"])
        self.assertFalse(result["evaluation_observed"])
        self.assertFalse(result["learning_observed"])

    def test_denied_authorization_is_still_recorded_as_denied(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="observe")
        record_authorization(
            trace, cycle, authorization_event_id="auth-denied", allowed=False
        )
        events = trace.to_list()
        authorization = events[-1]
        self.assertEqual(authorization["event"], "autonomy_authorization_observed")
        self.assertFalse(authorization["data"]["allowed"])

    def test_cycle_identity_is_unique(self):
        first = begin_cycle(DecisionTrace(), intent="observe")
        second = begin_cycle(DecisionTrace(), intent="observe")
        self.assertNotEqual(first.cycle_id, second.cycle_id)


    def test_task_evidence_links_goal_research_learning_by_stable_ids(self):
        from types import SimpleNamespace
        from decision_trace import TracePhase

        trace = DecisionTrace()
        trace.add(TracePhase.GOVERNANCE, "capability_decision", {"allowed": True})
        trace.add(TracePhase.EXECUTION, "execution_succeeded", {"identifier": "search"})
        trace.add(TracePhase.EVALUATION, "quality_scored", {"acceptable": True})
        trace.add(TracePhase.LEARNING, "goal_learning_recorded", {
            "goal_id": "goal-42", "subgoal_id": "sub-7", "facts": 2,
        })
        task = SimpleNamespace(
            id="task-research-99",
            typ=SimpleNamespace(value="research"),
            prompt="Research bounded question",
            retrieved_context={
                "autonomy_cycle_id": "cycle-fixed-1",
                "goal_id": "goal-42",
                "subgoal_id": "sub-7",
            },
            decision_trace=trace,
        )
        result = finalize_cycle_from_task(task)
        self.assertTrue(result["ok"])
        self.assertEqual(result["cycle_id"], "cycle-fixed-1")
        self.assertEqual(result["goal_id"], "goal-42")
        self.assertEqual(result["subgoal_id"], "sub-7")
        self.assertEqual(result["research_id"], "task-research-99")
        self.assertTrue(result["authorization_observed"])
        self.assertTrue(result["execution_observed"])
        self.assertTrue(result["evaluation_observed"])
        self.assertTrue(result["learning_observed"])

    def test_denied_authorization_never_records_execution(self):
        from types import SimpleNamespace
        from decision_trace import TracePhase

        trace = DecisionTrace()
        trace.add(TracePhase.GOVERNANCE, "capability_decision", {"allowed": False})
        task = SimpleNamespace(
            id="task-denied",
            typ=SimpleNamespace(value="research"),
            prompt="Denied research",
            retrieved_context={
                "autonomy_cycle_id": "cycle-denied",
                "goal_id": "goal-1",
                "subgoal_id": "sub-1",
            },
            decision_trace=trace,
        )
        result = finalize_cycle_from_task(task)
        self.assertTrue(result["ok"])
        self.assertTrue(result["authorization_denied"])
        self.assertFalse(result["execution_observed"])
        self.assertFalse(any(
            entry.event == "autonomy_execution_observed" for entry in trace.entries
        ))


    def test_decision_trace_auto_correlates_events_after_cycle_start(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, goal_id="goal-9", subgoal_id="sub-2", intent="bounded research")
        trace.add(TracePhase.CLASSIFICATION, "intent_interpreted", {"task_type": "research"})
        self.assertTrue(all(entry.data.get("cycle_id") == cycle.cycle_id for entry in trace.entries))

    def test_executor_prepares_background_cycle_with_real_memory_context(self):
        from executor import Executor, Task, TaskType, Strategy

        class FakeMemory:
            def build_retrieval_context(self, *args, **kwargs):
                return {"facts": ["remembered owner preference"]}

            def format_retrieval_context(self, context):
                return "Relevant remembered context: owner preference"

        task = Task(
            id="background-task-1",
            typ=TaskType.RESEARCH,
            prompt="Research a bounded owner goal",
            beschreibung="background goal",
            strategy=Strategy(allow_tools=False),
            interaction_class="NORMAL_CHAT",
            retrieved_context={
                "source": "goal_autonomy",
                "goal_id": "goal-9",
                "subgoal_id": "sub-2",
            },
        )
        executor = object.__new__(Executor)
        with patch("memory.get_memory", return_value=FakeMemory()):
            executor._prepare_autonomy_cycle(task)

        self.assertTrue(task.retrieved_context.get("autonomy_cycle_id"))
        self.assertIn("Relevant remembered context", task.prompt)
        names = {entry.event for entry in task.decision_trace.entries}
        self.assertIn("autonomy_observation_captured", names)
        self.assertIn("autonomy_intent_interpreted", names)
        self.assertIn("autonomy_memory_context_checked", names)
        self.assertIn("autonomy_goal_context_checked", names)
        self.assertIn("autonomy_plan_selected", names)
        self.assertTrue(all(
            entry.data.get("cycle_id") == task.retrieved_context["autonomy_cycle_id"]
            for entry in task.decision_trace.entries
        ))

    def test_task_cycle_finalization_does_not_invent_learning(self):
        from executor import Executor, Task, TaskType, TaskStatus
        from decision_trace import TracePhase

        task = Task(
            id="background-task-2",
            typ=TaskType.RESEARCH,
            prompt="Research a bounded owner goal",
            beschreibung="background goal",
            retrieved_context={
                "source": "goal_autonomy",
                "goal_id": "goal-9",
                "subgoal_id": "sub-2",
            },
        )
        executor = object.__new__(Executor)
        executor._prepare_autonomy_cycle(task)
        task.decision_trace.add(
            TracePhase.GOVERNANCE,
            "goal_scope_authorization_observed",
            {"goal_id": "goal-9", "subgoal_id": "sub-2", "allowed": True},
        )
        task.status = TaskStatus.DONE
        executor._finalize_autonomy_cycle(task)
        result = task.retrieved_context.get("autonomy_cycle_validation") or {}
        self.assertTrue(result.get("valid"))
        self.assertFalse(any(
            entry.event == "autonomy_learning_recorded" for entry in task.decision_trace.entries
        ))


if __name__ == "__main__":
    unittest.main()
