from __future__ import annotations

import asyncio
import unittest
from typing import Any
from types import SimpleNamespace
from unittest.mock import Mock, patch

from decision_trace import DecisionTrace, TracePhase
from executor import Executor, Strategy, Task, TaskStatus, TaskType, get_executor
from learning_engine import CandidateStatus, LearningCandidate, LearningEngine, get_learning_engine
from memory import EpistemicClass, Memory, get_memory
from evals.kernel_benchmark import run as run_kernel_benchmark
from evals.kernel_metrics import KernelMetricsEvaluator, KernelMetricsReport


class TestProveTheKernelPillars(unittest.TestCase):
    def setUp(self):
        self.executor = get_executor()
        self.executor._tasks.clear()
        self.memory = get_memory()
        self.learning = get_learning_engine()

    def test_pillar1_e2e_100_task_benchmark(self):
        """Pillar 1: Standardized 100-Task E2E Benchmark Pipeline."""
        res = run_kernel_benchmark()
        self.assertTrue(res["ok"])
        self.assertEqual(res["passed"], 100)
        self.assertEqual(res["total"], 100)
        self.assertGreaterEqual(res["metrics"]["autonomy_without_loss_of_control"], 0.9)

    def test_pillar2_task_graph_dag_integrity(self):
        """Pillar 2: Formal TaskGraph DAG model & cycle detection."""
        t_root = Task(id="root_1", typ=TaskType.PLAN, prompt="Main Plan Goal", beschreibung="Root Goal")
        t_sub1 = Task(id="sub_1", typ=TaskType.ANALYSIS, prompt="Subtask 1", beschreibung="Analysis", parent_id="root_1")
        t_sub2 = Task(id="sub_2", typ=TaskType.CODE, prompt="Subtask 2", beschreibung="Coding", parent_id="root_1")
        t_sub2.dependencies.append("sub_1")

        self.executor._tasks["root_1"] = t_root
        self.executor._tasks["sub_1"] = t_sub1
        self.executor._tasks["sub_2"] = t_sub2
        t_root.sub_task_ids.extend(["sub_1", "sub_2"])

        # Check graph retrieval
        graph = self.executor.get_task_graph("root_1")
        self.assertEqual(graph["root_id"], "root_1")
        self.assertEqual(graph["node_count"], 3)

        # Check DAG validity
        val_res = self.executor.validate_task_graph("root_1")
        self.assertTrue(val_res["is_valid"])
        self.assertFalse(val_res["has_cycle"])

        # Check dependencies
        self.assertFalse(self.executor.are_dependencies_satisfied("sub_2"))
        t_sub1.status = TaskStatus.DONE
        self.assertTrue(self.executor.are_dependencies_satisfied("sub_2"))

        # Test cycle detection
        t_sub1.dependencies.append("sub_2")
        val_cycle = self.executor.validate_task_graph("root_1")
        self.assertFalse(val_cycle["is_valid"])
        self.assertTrue(val_cycle["has_cycle"])

    def test_pillar3_formal_learning_commit_pipeline(self):
        """Pillar 3: Formal Learning Commit Pipeline & Evidence Verification."""
        t_ev = Task(id="ev_task_1", typ=TaskType.RESEARCH, prompt="Research Task", beschreibung="Evidence")
        t_ev.status = TaskStatus.DONE
        self.executor._tasks["ev_task_1"] = t_ev

        cand = self.learning.propose_candidate(
            observation="Observed efficient search query format",
            relevance_notes="Reduces web search latency",
            evidence_task_ids=["ev_task_1"],
            confidence=0.88,
        )
        self.assertEqual(cand.status, CandidateStatus.CANDIDATE)

        # Verify evidence
        ev_res = self.learning.verify_candidate_evidence(cand.candidate_id, require_evidence_tasks=True)
        self.assertTrue(ev_res["verified"])

        # Evaluate candidate
        self.learning.evaluate_candidate(
            candidate_id=cand.candidate_id,
            replay_passed=True,
            eval_score_gain=0.15,
            regression_check_passed=True,
            governance_approved=True,
        )

        # Commit candidate with evidence verification
        committed = self.learning.commit_candidate(cand.candidate_id, verify_evidence=True)
        self.assertIsNotNone(committed)
        self.assertEqual(committed.status, CandidateStatus.COMMITTED)
        self.assertEqual(len(committed.commit_hash), 16)

    def test_pillar4_epistemic_memory_and_contradiction_handling(self):
        """Pillar 4: Epistemic Memory classes, evidence linking & contradiction resolution."""
        mem_entry = self.memory.add_epistemic_memory(
            key="user_preference_concise",
            value="User prefers bullet points",
            epistemic_class=EpistemicClass.USER_ASSERTION,
            source="steffen",
            source_authority="owner",
            confidence=0.9,
        )
        self.assertEqual(mem_entry.epistemic_class, EpistemicClass.USER_ASSERTION)
        self.assertEqual(mem_entry.source_authority, "owner")

        # Link evidence task
        linked = self.memory.link_evidence_to_memory(mem_entry.memory_id, task_id="task_proof_4", confidence_boost=0.05)
        self.assertIn("task_proof_4", linked.evidence_task_ids)
        self.assertAlmostEqual(linked.confidence, 0.95)

        # Resolve contradiction
        contradicted = self.memory.resolve_contradiction(
            memory_id=mem_entry.memory_id,
            contradicting_ref="task_proof_5",
            new_epistemic_class=EpistemicClass.CONTRADICTED,
            new_confidence=0.1,
        )
        self.assertEqual(contradicted.epistemic_class, EpistemicClass.CONTRADICTED)
        self.assertIn("task_proof_5", contradicted.contradicted_by)
        self.assertAlmostEqual(contradicted.confidence, 0.1)

    def test_pillar5_autonomy_governance_metrics_evaluator(self):
        """Pillar 5: Objective Autonomy & Governance Metrics calculation."""
        tasks = []
        for i in range(10):
            t = Task(id=f"metric_t_{i}", typ=TaskType.CHAT, prompt=f"Prompt {i}", beschreibung="Desc")
            t.status = TaskStatus.DONE
            t.record_action("classify", {"intent": "chat"})
            t.record_evidence("test", "good", 1.0)
            t.decision_trace = DecisionTrace()
            for phase in TracePhase:
                t.decision_trace.add(phase, f"event_{phase.value}", {"status": "ok"})
            tasks.append(t)

        evaluator = KernelMetricsEvaluator()
        report = evaluator.evaluate_tasks(tasks)

        self.assertEqual(report.total_tasks, 10)
        self.assertEqual(report.successful_tasks, 10)
        self.assertEqual(report.task_success_rate, 1.0)
        self.assertEqual(report.unauthorized_action_rate, 0.0)
        self.assertEqual(report.trace_completeness, 1.0)
        self.assertEqual(report.autonomy_without_loss_of_control, 1.0)


class TestLearningEvidenceVerification(unittest.TestCase):
    def setUp(self):
        self.learning = LearningEngine()
        self.candidate = LearningCandidate(
            candidate_id="evidence_candidate",
            ts=0.0,
            observation="Korrektur einer fehlgeschlagenen Aufgabe",
            relevance_notes="Regressionstest",
            evidence_task_ids=["evidence_task"],
        )
        self.lookup = Mock()
        self.executor = SimpleNamespace(get_task=self.lookup)
        candidate_patch = patch.object(
            self.learning, "get_candidate", return_value=self.candidate
        )
        candidate_patch.start()
        self.addCleanup(candidate_patch.stop)
        executor_patch = patch("executor.get_executor", return_value=self.executor)
        self.get_executor = executor_patch.start()
        self.addCleanup(executor_patch.stop)

    def _task(self, task_id="evidence_task", traced=False):
        task = Task(
            id=task_id,
            typ=TaskType.RESEARCH,
            prompt="Evidenz prüfen",
            beschreibung="Test-Evidenz",
        )
        if traced:
            task.decision_trace.add(
                TracePhase.EXECUTION, "execution_failed", {"ok": False}
            )
        return task

    def test_bug_evidence_executor_error_fails_closed(self):
        self.get_executor.side_effect = RuntimeError("private detail")
        result = self.learning.verify_candidate_evidence(self.candidate.candidate_id)
        self.assertFalse(result["verified"])
        self.assertEqual(result["valid_task_count"], 0)
        self.assertNotIn("private detail", result["error"])

    def test_bug_evidence_lookup_error_after_valid_task_fails_closed(self):
        self.candidate.evidence_task_ids = ["first", "second"]
        self.lookup.side_effect = [self._task("first"), RuntimeError("lookup failed")]
        result = self.learning.verify_candidate_evidence(self.candidate.candidate_id)
        self.assertFalse(result["verified"])
        self.assertEqual(result["valid_task_count"], 1)

    def test_bug_evidence_requires_every_linked_task(self):
        self.candidate.evidence_task_ids = ["first", "missing", "last"]
        tasks = {"first": self._task("first"), "last": self._task("last")}
        self.lookup.side_effect = tasks.get
        result = self.learning.verify_candidate_evidence(self.candidate.candidate_id)
        self.assertFalse(result["verified"])
        self.assertEqual(result["evidence_task_count"], 3)
        self.assertEqual(result["valid_task_count"], 2)
        self.assertEqual(result["missing_task_ids"], ["missing"])
        self.assertEqual(self.lookup.call_count, 3)

    def test_bug_evidence_optional_does_not_accept_broken_references(self):
        self.lookup.return_value = None
        result = self.learning.verify_candidate_evidence(
            self.candidate.candidate_id, require_evidence_tasks=False
        )
        self.assertFalse(result["verified"])

    def test_bug_evidence_trace_remains_optional_by_default(self):
        self.lookup.return_value = self._task()
        result = self.learning.verify_candidate_evidence(self.candidate.candidate_id)
        self.assertTrue(result["verified"])

    def test_bug_evidence_trace_requirement_rejects_absent_or_empty_trace(self):
        for trace in (None, DecisionTrace(), {"entries": ["untyped"]}):
            with self.subTest(trace=trace):
                task = self._task()
                task.decision_trace = trace
                self.lookup.return_value = task
                result = self.learning.verify_candidate_evidence(
                    self.candidate.candidate_id, require_decision_trace=True
                )
                self.assertFalse(result["verified"])
                self.assertEqual(result["missing_trace_task_ids"], ["evidence_task"])

    def test_bug_evidence_trace_required_for_every_task(self):
        self.candidate.evidence_task_ids = ["traced", "untraced"]
        tasks = {
            "traced": self._task("traced", traced=True),
            "untraced": self._task("untraced"),
        }
        self.lookup.side_effect = tasks.get
        result = self.learning.verify_candidate_evidence(
            self.candidate.candidate_id, require_decision_trace=True
        )
        self.assertFalse(result["verified"])
        self.assertEqual(result["missing_trace_task_ids"], ["untraced"])

    def test_bug_evidence_failure_trace_can_support_learning(self):
        task = self._task(traced=True)
        task.status = TaskStatus.FAILED
        self.lookup.return_value = task
        result = self.learning.verify_candidate_evidence(
            self.candidate.candidate_id, require_decision_trace=True
        )
        self.assertTrue(result["verified"])
        self.assertEqual(result["valid_task_count"], 1)
        self.assertFalse(self.candidate.replay_passed)
        self.assertFalse(self.candidate.regression_check_passed)
        self.assertFalse(self.candidate.governance_approved)
        self.assertEqual(self.candidate.status, CandidateStatus.CANDIDATE)

    def test_bug_evidence_empty_ids_respect_both_requirements(self):
        self.candidate.evidence_task_ids = []
        for require_tasks, require_trace, expected in (
            (True, False, False), (True, True, False),
            (False, True, False), (False, False, True),
        ):
            with self.subTest(require_tasks=require_tasks, require_trace=require_trace):
                result = self.learning.verify_candidate_evidence(
                    self.candidate.candidate_id,
                    require_evidence_tasks=require_tasks,
                    require_decision_trace=require_trace,
                )
                self.assertEqual(result["verified"], expected)
        self.get_executor.assert_not_called()

    def test_bug_evidence_missing_candidate_is_rejected(self):
        with patch.object(self.learning, "get_candidate", return_value=None):
            result = self.learning.verify_candidate_evidence("missing")
        self.assertFalse(result["verified"])
        self.get_executor.assert_not_called()

    def test_bug_unverifiable_evidence_blocks_commit_even_with_passed_evaluations(self):
        self.candidate.replay_passed = True
        self.candidate.regression_check_passed = True
        self.candidate.governance_approved = True
        self.get_executor.side_effect = RuntimeError("unavailable")
        with patch.object(self.learning, "_save_candidate") as save:
            result = self.learning.commit_candidate(
                self.candidate.candidate_id, verify_evidence=True
            )
        self.assertEqual(result.status, CandidateStatus.REJECTED)
        self.assertEqual(result.commit_hash, "")
        save.assert_called_once_with(result)


if __name__ == "__main__":
    unittest.main()
