from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from decision_trace import TracePhase
from executor import Executor, Task, TaskStatus, TaskType
from goal_store import GoalStore, IsaacSubgoal, OwnerGoal
from isaac_30day_evidence import read_events
from isaac_autonomy_cycle import begin_cycle, record_authorization, record_evaluation, record_execution
from isaac_runtime_audit import (
    AUDIT_CONTRACT,
    REQUIRED_SURFACES,
    audit_hook_inventory,
    audited_surface,
    bind_action_id,
    emit_proof_audit_readiness,
)
from motivation import MotivationDecision, _record_research_learning_and_interest


class TestRuntimeAuditIntegration(unittest.TestCase):
    def setUp(self):
        self._old_env = {
            key: os.environ.get(key)
            for key in ("ISAAC_30DAY_EVIDENCE_DIR", "ISAAC_30DAY_OFFICIAL")
        }
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["ISAAC_30DAY_EVIDENCE_DIR"] = self._tmp.name
        os.environ["ISAAC_30DAY_OFFICIAL"] = "1"

    def tearDown(self):
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def test_decorated_runtime_path_emits_correlated_start_and_finish(self):
        @audited_surface("executor_tools")
        def example_tool():
            return {"ok": True}

        with bind_action_id("executor-auth-123"):
            result = example_tool()
        self.assertTrue(result["ok"])
        events = read_events(Path(self._tmp.name))
        self.assertEqual([e["event_type"] for e in events], [
            "runtime_surface_event", "runtime_surface_event"
        ])
        start, finish = [e["payload"] for e in events]
        self.assertEqual(start["contract"], AUDIT_CONTRACT)
        self.assertEqual(start["surface"], "executor_tools")
        self.assertEqual(start["phase"], "started")
        self.assertEqual(finish["phase"], "completed")
        self.assertEqual(start["action_id"], finish["action_id"])
        self.assertEqual(start["action_id"], "executor-auth-123")
        self.assertTrue(finish["ok"])

    def test_production_hook_inventory_covers_all_required_surfaces(self):
        inventory = audit_hook_inventory()
        self.assertTrue(inventory["coverage_complete"], inventory["missing_hooks"])
        self.assertEqual(set(inventory["surfaces"]), set(REQUIRED_SURFACES))
        for surface in REQUIRED_SURFACES:
            self.assertTrue(inventory["hooks"][surface], surface)

    def test_readiness_event_is_derived_from_real_hook_inventory(self):
        inventory = emit_proof_audit_readiness()
        self.assertTrue(inventory["coverage_complete"])
        events = read_events(Path(self._tmp.name))
        readiness = [e for e in events if e["event_type"] == "proof_audit_readiness"]
        self.assertEqual(len(readiness), 1)
        payload = readiness[0]["payload"]
        self.assertTrue(payload["coverage_complete"])
        self.assertTrue(payload["verified_at_runtime"])
        self.assertEqual(set(payload["surfaces"]), set(REQUIRED_SURFACES))
        self.assertEqual(payload["contract"], AUDIT_CONTRACT)

    def test_real_research_execution_records_causal_learning_and_bounded_interest(self):
        goal_store = GoalStore(path=Path(self._tmp.name) / "goals.json")
        goal_store.goals["goal-1"] = OwnerGoal(
            id="goal-1", title="Improve Isaac causal memory", status="active"
        )
        goal_store.subgoals["sub-1"] = IsaacSubgoal(
            id="sub-1", parent_goal_id="goal-1",
            title="Validate evidence-linked research", status="active",
        )
        task = Task(
            id="research-task-1",
            typ=TaskType.RESEARCH,
            prompt="Research evidence-linked causal memory",
            beschreibung="Research evidence-linked causal memory",
            retrieved_context={"goal_id": "goal-1", "subgoal_id": "sub-1", "source": "goal_autonomy"},
        )
        cycle = begin_cycle(
            task.decision_trace,
            goal_id="goal-1",
            subgoal_id="sub-1",
            intent=task.prompt,
        )
        task.retrieved_context["autonomy_cycle_id"] = cycle.cycle_id
        auth_entry = task.decision_trace.add(
            TracePhase.GOVERNANCE,
            "goal_autonomy_authorization_observed",
            {"cycle_id": cycle.cycle_id, "allowed": True},
        )
        record_authorization(
            task.decision_trace, cycle,
            authorization_event_id=auth_entry.event_id, allowed=True,
        )
        decision = MotivationDecision(
            goal_id="goal-1",
            subgoal_id="sub-1",
            goal_title="Improve Isaac causal memory",
            subgoal_title="Validate evidence-linked research",
            score=7.5,
            reason="bounded research",
            suggested_task_type="research",
            allow_tools=True,
            prompt=task.prompt,
        )
        pre_state = {
            "task_status": task.status.value,
            "trace_entry_count": len(task.decision_trace.entries),
            "score_total": None,
            "goal_id": "goal-1",
            "subgoal_id": "sub-1",
        }

        class FakeSearch:
            async def search(self, query, **kwargs):
                hit = SimpleNamespace(
                    titel="Causal memory paper",
                    snippet="A reproducible evaluation of evidence-linked decisions.",
                    url="https://example.org/paper?token=must-not-be-recorded",
                    quelle="example.org",
                )
                return SimpleNamespace(
                    hits=[hit],
                    abstract="",
                    quellen=["example.org"],
                    als_kontext=lambda max_hits=12: (
                        "Causal memory paper. Source: https://example.org/paper"
                    ),
                )

        answer = (
            "The evidence supports linking research outputs to subsequent evaluations. "
            "A useful next step is to compare two bounded approaches in a controlled test."
        )
        executor = Executor.__new__(Executor)
        executor._maybe_use_tool = AsyncMock(return_value=("", ""))
        executor._get_search = lambda: FakeSearch()
        executor.relay = SimpleNamespace(
            ask_with_fallback=AsyncMock(return_value=(answer, "test-provider"))
        )
        executor.logic = SimpleNamespace(
            evaluate=lambda *args: SimpleNamespace(total=0.82, acceptable=True)
        )
        executor._notify = lambda _task: None

        asyncio.run(executor._execute_research(task))
        self.assertEqual(task.status, TaskStatus.DONE)
        source_entries = [
            entry for entry in task.decision_trace.entries
            if entry.event == "research_sources_collected"
        ]
        evaluation_entries = [
            entry for entry in task.decision_trace.entries
            if entry.phase == TracePhase.EVALUATION and entry.event == "quality_scored"
        ]
        self.assertTrue(source_entries)
        self.assertTrue(evaluation_entries)
        self.assertNotIn("token=must-not-be-recorded", repr(source_entries[-1].data))

        record_execution(
            task.decision_trace, cycle,
            execution_event_id=source_entries[-1].event_id,
        )
        record_evaluation(
            task.decision_trace, cycle,
            evaluation_event_id=evaluation_entries[-1].event_id,
            outcome=task.status.value,
        )
        result = _record_research_learning_and_interest(
            task, decision, cycle, goal_store, pre_state
        )
        self.assertTrue(result["recorded"], result)
        self.assertTrue(result["interest_recorded"], result)

        # Repeat the same real executor/evaluation path for a second independent
        # research cycle; two derivations must be produced from two real runs.
        task2 = Task(
            id="research-task-2",
            typ=TaskType.RESEARCH,
            prompt="Compare bounded approaches for causal memory",
            beschreibung="Compare bounded approaches for causal memory",
            retrieved_context={"goal_id": "goal-1", "subgoal_id": "sub-1", "source": "goal_autonomy"},
        )
        cycle2 = begin_cycle(
            task2.decision_trace,
            goal_id="goal-1",
            subgoal_id="sub-1",
            intent=task2.prompt,
        )
        task2.retrieved_context["autonomy_cycle_id"] = cycle2.cycle_id
        auth_entry2 = task2.decision_trace.add(
            TracePhase.GOVERNANCE,
            "goal_autonomy_authorization_observed",
            {"cycle_id": cycle2.cycle_id, "allowed": True},
        )
        record_authorization(
            task2.decision_trace, cycle2,
            authorization_event_id=auth_entry2.event_id, allowed=True,
        )
        decision2 = MotivationDecision(
            goal_id="goal-1",
            subgoal_id="sub-1",
            goal_title="Improve Isaac causal memory",
            subgoal_title="Validate evidence-linked research",
            score=7.5,
            reason="independent bounded research",
            suggested_task_type="research",
            allow_tools=True,
            prompt=task2.prompt,
        )
        pre_state2 = {
            "task_status": task2.status.value,
            "trace_entry_count": len(task2.decision_trace.entries),
            "score_total": None,
            "goal_id": "goal-1",
            "subgoal_id": "sub-1",
        }
        asyncio.run(executor._execute_research(task2))
        source_entries2 = [
            entry for entry in task2.decision_trace.entries
            if entry.event == "research_sources_collected"
        ]
        evaluation_entries2 = [
            entry for entry in task2.decision_trace.entries
            if entry.phase == TracePhase.EVALUATION and entry.event == "quality_scored"
        ]
        self.assertTrue(source_entries2)
        self.assertTrue(evaluation_entries2)
        record_execution(
            task2.decision_trace, cycle2,
            execution_event_id=source_entries2[-1].event_id,
        )
        record_evaluation(
            task2.decision_trace, cycle2,
            evaluation_event_id=evaluation_entries2[-1].event_id,
            outcome=task2.status.value,
        )
        result2 = _record_research_learning_and_interest(
            task2, decision2, cycle2, goal_store, pre_state2
        )
        self.assertTrue(result2["recorded"], result2)
        self.assertTrue(result2["interest_recorded"], result2)

        events = read_events(Path(self._tmp.name))
        learning = [
            event for event in events
            if event["event_type"] == "research_cycle_completed"
        ]
        interests = [
            event for event in events
            if event["event_type"] == "interest_derivation_recorded"
        ]
        source_evidence = [
            event for event in events
            if event["event_type"] == "research_sources_collected"
        ]
        self.assertEqual(len(learning), 2)
        self.assertEqual(len(interests), 2)
        self.assertEqual(len(source_evidence), 2)
        self.assertNotIn("token=must-not-be-recorded", repr(source_evidence[0]["payload"]))
        self.assertNotIn("The evidence supports", interests[0]["payload"]["new_information"])
        self.assertEqual(learning[0]["payload"]["source_cycle_id"], cycle.cycle_id)
        self.assertEqual(learning[0]["payload"]["research_id"], task.id)
        self.assertEqual(learning[1]["payload"]["research_id"], task2.id)
        self.assertNotEqual(learning[0]["payload"]["source_cycle_id"], learning[1]["payload"]["source_cycle_id"])
        self.assertEqual(interests[0]["payload"]["observation_research_id"], task.id)
        self.assertEqual(interests[1]["payload"]["observation_research_id"], task2.id)


if __name__ == "__main__":
    unittest.main()
