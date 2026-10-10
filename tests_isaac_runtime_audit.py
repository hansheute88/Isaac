from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from isaac_30day_evidence import read_events
from isaac_runtime_audit import (
    AUDIT_CONTRACT,
    REQUIRED_SURFACES,
    audit_hook_inventory,
    audited_surface,
    emit_proof_audit_readiness,
)


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


if __name__ == "__main__":
    unittest.main()
