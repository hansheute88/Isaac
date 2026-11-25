"""Regressionen gegen falsche Zielabschlüsse und falsch gebundene Ergebnisse."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from goal_inquiry import record_goal_learning_from_task
from goal_store import GoalStore, OwnerGoal


class TestGoalCompletion(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = GoalStore(Path(tmp.name) / "goals.json")
        self.goal = OwnerGoal(
            id="goal_test",
            title="Prototyp erstellen",
            success_criteria="prototyp fertig getestet",
        )
        self.store.goals[self.goal.id] = self.goal
        self.subgoal = self.store.add_subgoal(self.goal.id, "Prototyp testen")
        self.memory = Mock()
        for target, value in (
            ("goal_inquiry.get_goal_store", self.store),
            ("memory.get_memory", self.memory),
            ("goal_inquiry.register_inquiries_from_text", []),
            ("goal_inquiry.subgoal_done_min_score", 5.5),
            ("goal_inquiry.max_subgoal_attempts", 8),
            ("audit.AuditLog.action", None),
        ):
            patcher = patch(target, return_value=value)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
            if target.endswith("register_inquiries_from_text"):
                self.inquiries = mock

    def task(self, *, status="done", score=8.0, mode="work"):
        return SimpleNamespace(
            id="goal_task",
            retrieved_context={
                "goal_id": self.goal.id,
                "subgoal_id": self.subgoal.id,
                "mode": mode,
            },
            antwort="Der Prototyp ist fertig und getestet.",
            status=SimpleNamespace(value=status),
            score=SimpleNamespace(total=score),
        )

    def test_bug_incomplete_sibling_blocks_parent_completion(self):
        self.subgoal.status = "done"
        sibling = self.store.add_subgoal(self.goal.id, "Weitere Voraussetzung")
        for state in ("active", "paused", "failed", "unknown"):
            with self.subTest(state=state):
                sibling.status = state
                self.assertFalse(self.store.maybe_complete_goal(self.goal.id))
                self.assertEqual(self.goal.status, "active")

    def test_bug_all_done_completion_survives_reload(self):
        self.subgoal.status = "done"
        sibling = self.store.add_subgoal(self.goal.id, "Weitere Voraussetzung")
        sibling.status = "done"
        self.assertTrue(self.store.maybe_complete_goal(self.goal.id))
        reloaded = GoalStore(self.store.path)
        self.assertEqual(reloaded.goals[self.goal.id].status, "done")
        self.assertFalse(reloaded.maybe_complete_goal(self.goal.id))

    def test_bug_empty_goal_is_not_complete(self):
        self.store.subgoals.clear()
        self.assertFalse(self.store.maybe_complete_goal(self.goal.id))

    def test_bug_keywords_cannot_override_task_status(self):
        for status in ("failed", "error", "cancelled", "running", "pending"):
            with self.subTest(status=status):
                out = record_goal_learning_from_task(self.task(status=status))
                self.assertNotEqual(out.get("subgoal_status"), "done")
                self.assertEqual(self.subgoal.status, "active")
                self.assertEqual(self.goal.status, "active")

    def test_bug_keywords_cannot_override_score(self):
        out = record_goal_learning_from_task(self.task(score=4.0))
        self.assertTrue(out["criteria_hit"])
        self.assertEqual(self.subgoal.status, "active")
        self.assertEqual(self.goal.status, "active")

    def test_bug_keywords_cannot_skip_other_subgoals(self):
        sibling = self.store.add_subgoal(self.goal.id, "Dokumentation")
        out = record_goal_learning_from_task(self.task())
        self.assertEqual(out["subgoal_status"], "done")
        self.assertEqual(sibling.status, "active")
        self.assertEqual(self.goal.status, "active")

    def test_bug_planning_and_questions_do_not_complete_work(self):
        for mode in ("plan", "inquiry", "unknown", " PLAN "):
            with self.subTest(mode=mode):
                out = record_goal_learning_from_task(self.task(mode=mode))
                self.assertNotEqual(out.get("subgoal_status"), "done")
                self.assertEqual(self.subgoal.status, "active")
                self.assertEqual(self.goal.status, "active")

    def test_bug_legacy_planning_header_does_not_complete_work(self):
        task = self.task(mode="")
        task.prompt = "[Goal-Autonomie · mode=plan]\\nOwner-Ziel: Prototyp"
        out = record_goal_learning_from_task(task)
        self.assertNotEqual(out.get("subgoal_status"), "done")
        self.assertEqual(self.goal.status, "active")

    def test_bug_unavailable_goal_store_rejects_result(self):
        with patch("goal_inquiry.get_goal_store", side_effect=OSError("private")):
            out = record_goal_learning_from_task(self.task())
        self.assertEqual(out, {"ok": False, "reason": "goal_store_unavailable"})
        self.memory.set_fact.assert_not_called()
        self.inquiries.assert_not_called()

    def test_goal_only_progress_remains_supported(self):
        task = self.task()
        task.retrieved_context.pop("subgoal_id")
        out = record_goal_learning_from_task(task)
        self.assertTrue(out["ok"])
        self.assertEqual(out["facts"], 2)
        self.assertEqual(self.subgoal.status, "active")
        self.assertEqual(self.goal.status, "active")

    def test_bug_successful_work_and_research_can_complete_subgoal(self):
        for mode in ("work", "research", ""):
            with self.subTest(mode=mode):
                self.goal.status = "active"
                self.subgoal.status = "active"
                out = record_goal_learning_from_task(self.task(mode=mode))
                self.assertEqual(out["subgoal_status"], "done")
                self.assertEqual(out["goal_status"], "done")

    def test_bug_inactive_goal_rejects_late_result_before_memory_writes(self):
        for state in ("paused", "done", "failed"):
            with self.subTest(state=state):
                self.goal.status = state
                out = record_goal_learning_from_task(self.task())
                self.assertFalse(out["ok"])
                self.assertEqual(out["reason"], "inactive_goal")
                self.assertEqual(self.goal.status, state)
                self.assertEqual(self.subgoal.status, "active")
        self.memory.set_fact.assert_not_called()
        self.inquiries.assert_not_called()

    def test_bug_unknown_goal_rejects_result(self):
        task = self.task()
        task.retrieved_context["goal_id"] = "missing"
        out = record_goal_learning_from_task(task)
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "unknown_goal")
        self.memory.set_fact.assert_not_called()
        self.inquiries.assert_not_called()

    def test_bug_foreign_or_missing_subgoal_rejects_result(self):
        other = OwnerGoal(id="other_goal", title="Anderes Ziel")
        self.store.goals[other.id] = other
        foreign = self.store.add_subgoal(other.id, "Andere Aufgabe")
        for sid in (foreign.id, "missing"):
            with self.subTest(sid=sid):
                task = self.task()
                task.retrieved_context["subgoal_id"] = sid
                out = record_goal_learning_from_task(task)
                self.assertFalse(out["ok"])
                self.assertEqual(out["reason"], "invalid_subgoal")
        self.assertEqual(foreign.status, "active")
        self.memory.set_fact.assert_not_called()
        self.inquiries.assert_not_called()


if __name__ == "__main__":
    unittest.main()
