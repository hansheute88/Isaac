"""Opt-in RED tests for missing action-bound authorization.

Expected to FAIL on pinned baseline; run explicitly in disposable environment:
    python3 -m unittest -v tests_isaac_p0_governance_red

DO NOT include in the required green CI gate until the hardening implementation.
The mocked sink models an external effect; no actual network/file/shell action occurs.
"""
from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from executor import Executor, Task, TaskType
from isaac_capabilities import RWXRegistry
import tool_runtime


class TestP0ActionBoundaryMustFailClosed(unittest.TestCase):
    def test_missing_declaration_must_not_satisfy_execute_capability(self):
        executor = object.__new__(Executor)
        executor.rwx_registry = RWXRegistry()
        task = Task(
            id="p0-no-declaration",
            typ=TaskType.CODE,
            prompt="run protected tool",
            beschreibung="security invariant, currently red",
            required_capabilities=[],
        )
        error = executor._check_tool_execution_capability(
            task, {"identifier": "protected-tool", "name": "Protected"}
        )
        self.assertIsNotNone(error, "Missing declaration cannot be an authorization")

    def test_direct_selected_tool_must_require_action_bound_authorization(self):
        selection = {
            "source": "registry", "identifier": "protected-tool",
            "name": "Protected", "kind": "script", "tool": object(),
        }
        sink = AsyncMock(return_value={"ok": True, "output": "effect-faked"})
        # Allow the legacy Constitution check to isolate the missing per-action
        # authorization. No R/W/X gate is mocked here.
        with patch.object(tool_runtime, "constitution_gate_for_tool", return_value=None), \
             patch.object(tool_runtime, "_run_registry_tool", sink):
            result = asyncio.run(tool_runtime.run_selected_tool(selection, "mocked effect"))
        sink.assert_not_awaited()  # RED: the effect sink is currently reached
        self.assertFalse(result["ok"])

    def test_skip_constitution_without_proof_must_not_reach_effect(self):
        selection = {
            "source": "registry", "identifier": "protected-tool",
            "name": "Protected", "kind": "script", "tool": object(),
        }
        sink = AsyncMock(return_value={"ok": True, "output": "effect-faked"})
        with patch.object(tool_runtime, "_run_registry_tool", sink):
            result = asyncio.run(tool_runtime.run_selected_tool(
                selection, "mocked effect", skip_constitution=True
            ))
        sink.assert_not_awaited()  # RED: no independently verified proof supplied
        self.assertFalse(result["ok"])

    def test_direct_run_tool_must_not_reach_effect_without_proof(self):
        sink = AsyncMock(return_value={"ok": True, "output": "effect-faked"})
        with patch.object(tool_runtime, "_run_registry_tool", sink):
            result = asyncio.run(tool_runtime.run_tool(object(), "mocked effect"))
        sink.assert_not_awaited()  # RED: direct path has no proof validation
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
