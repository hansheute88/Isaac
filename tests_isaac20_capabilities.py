from __future__ import annotations

import unittest

from isaac_capabilities import (
    Capability,
    CapabilityRequest,
    RWXPolicy,
    RWXRegistry,
    capability_from_legacy_action,
    evaluate_with_audit,
)


class TestIsaac20CapabilityLiveEvidence(unittest.TestCase):
    """Live-Pfad: ohne Deklaration wird R/W/X beratend auditiert, nie blockierend."""

    def _search_task(self):
        from executor import TaskType, get_executor

        executor = get_executor()
        return executor.create_task(
            typ=TaskType.SEARCH,
            prompt="Suche: Wetter Berlin",
            beschreibung="Suche: Wetter Berlin",
        )

    def test_undeclared_tool_capability_is_advisory(self):
        from executor import get_executor

        executor = get_executor()
        task = self._search_task()

        block = executor._check_tool_execution_capability(
            task, {"identifier": "web_search", "name": "web_search"}
        )

        self.assertIsNone(block)
        entries = [
            entry for entry in task.decision_trace.entries
            if entry.event == "tool_execution_capability"
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].data["mode"], "advisory")
        self.assertFalse(entries[0].data["declared"])
        self.assertFalse(entries[0].data["allowed"])
        self.assertIn("tool_capability_advisory_trace_event_id", task.causal_refs)

    def test_declared_and_denied_tool_capability_still_blocks(self):
        from executor import get_executor

        executor = get_executor()
        task = self._search_task()
        task.required_capabilities.append(
            {"resource": "tool:web_search", "capability": "execute", "reason": "test"}
        )

        block = executor._check_tool_execution_capability(
            task, {"identifier": "web_search", "name": "web_search"}
        )

        self.assertIsNotNone(block)
        self.assertIn("R/W/X blockiert", block)


class TestIsaac20Capabilities(unittest.TestCase):
    def test_default_is_implicit_deny(self):
        decision = RWXRegistry().evaluate(
            CapabilityRequest("filesystem:/workspace", Capability.WRITE)
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_source, "implicit-deny")

    def test_explicit_read_write_without_execute(self):
        registry = RWXRegistry()
        registry.set_policy(
            RWXPolicy(
                resource="filesystem:/workspace",
                read=True,
                write=True,
                execute=False,
                source="test",
            )
        )
        self.assertTrue(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "read")
            ).allowed
        )
        self.assertTrue(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "write")
            ).allowed
        )
        self.assertFalse(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "execute")
            ).allowed
        )

    def test_decision_contains_audit_relevant_evidence(self):
        registry = RWXRegistry()
        registry.set_policy(
            RWXPolicy("tool:browser", execute=True, source="owner-policy", version=3)
        )
        decision = registry.evaluate(
            CapabilityRequest(
                "tool:browser",
                Capability.EXECUTE,
                principal="task:123",
                reason="open requested page",
                task_id="123",
            )
        )
        data = decision.as_dict()
        self.assertTrue(data["allowed"])
        self.assertEqual(data["policy_source"], "owner-policy")
        self.assertEqual(data["policy_version"], 3)
        self.assertEqual(data["task_id"], "123")

    def test_evaluate_with_audit_returns_same_decision(self):
        registry = RWXRegistry()
        registry.set_policy(RWXPolicy("tool:browser", execute=True, source="test"))
        decision = evaluate_with_audit(
            registry,
            CapabilityRequest("tool:browser", "execute", task_id="audit-test"),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.task_id, "audit-test")

    def test_executor_enforces_declared_capability(self):
        from executor import Executor, Task, TaskType

        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        task = Task(
            id="rwx-test",
            typ=TaskType.FILE,
            prompt="write test file",
            beschreibung="R/W/X regression",
            required_capabilities=[
                {"resource": "filesystem:/workspace", "capability": "write"}
            ],
        )
        self.assertIn("R/W/X blockiert", executor._check_required_capabilities(task))

        executor.set_capability_policy(
            RWXPolicy("filesystem:/workspace", write=True, source="test")
        )
        self.assertIsNone(executor._check_required_capabilities(task))
        self.assertTrue(any(
            entry.event == "capability_decision"
            for entry in task.decision_trace.entries
        ))

    def test_tool_execution_boundary_denies_without_explicit_policy(self):
        from executor import Executor, Task, TaskType

        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        task = Task(
            id="tool-rwx-deny",
            typ=TaskType.CODE,
            prompt="use protected tool",
            beschreibung="tool execution boundary",
            required_capabilities=[
                {"resource": "tool:protected-tool", "capability": "execute"}
            ],
        )
        error = executor._check_tool_execution_capability(
            task,
            {"identifier": "protected-tool", "name": "Protected"},
        )
        self.assertIn("R/W/X blockiert", error)
        self.assertTrue(any(
            entry.event == "tool_execution_capability"
            for entry in task.decision_trace.entries
        ))

    def test_tool_execution_boundary_allows_explicit_policy(self):
        from executor import Executor, Task, TaskType

        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        executor.set_capability_policy(
            RWXPolicy("tool:protected-tool", execute=True, source="tool-policy")
        )
        task = Task(
            id="tool-rwx-allow",
            typ=TaskType.CODE,
            prompt="use protected tool",
            beschreibung="tool execution boundary",
            required_capabilities=[
                {"resource": "tool:protected-tool", "capability": "execute"}
            ],
        )
        self.assertIsNone(
            executor._check_tool_execution_capability(
                task,
                {"identifier": "protected-tool", "name": "Protected"},
            )
        )

    def test_legacy_mapping_is_additive(self):
        self.assertEqual(capability_from_legacy_action("file_read"), Capability.READ)
        self.assertEqual(capability_from_legacy_action("file_write"), Capability.WRITE)
        self.assertEqual(capability_from_legacy_action("system_command"), Capability.EXECUTE)


if __name__ == "__main__":
    unittest.main()
