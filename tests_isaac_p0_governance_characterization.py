"""G1/G3 characterization: present behavior only. No production code changes.

Run: python3 -m unittest -v tests_isaac_p0_governance_characterization
"""
from __future__ import annotations

import unittest

from executor import Executor, Task, TaskType
from isaac_capabilities import RWXRegistry


class TestPresentCapabilityBehavior(unittest.TestCase):
    def test_missing_tool_declaration_currently_skips_rwx(self):
        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        task = Task(
            id="p0-legacy-undeclared",
            typ=TaskType.CODE,
            prompt="run protected tool",
            beschreibung="characterize compatibility branch",
            required_capabilities=[],
        )
        before = len(task.decision_trace.entries)
        result = executor._check_tool_execution_capability(
            task, {"identifier": "protected-tool", "name": "Protected"}
        )
        self.assertIsNone(result)  # OBSERVED legacy behavior, not desired policy
        self.assertEqual(len(task.decision_trace.entries), before)

    def test_declared_tool_without_policy_is_denied(self):
        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        task = Task(
            id="p0-explicit-deny",
            typ=TaskType.CODE,
            prompt="run protected tool",
            beschreibung="characterize explicit R/W/X",
            required_capabilities=[
                {"resource": "tool:protected-tool", "capability": "execute"}
            ],
        )
        result = executor._check_tool_execution_capability(
            task, {"identifier": "protected-tool", "name": "Protected"}
        )
        self.assertIsInstance(result, str)
        self.assertIn("R/W/X blockiert", result)


if __name__ == "__main__":
    unittest.main()
