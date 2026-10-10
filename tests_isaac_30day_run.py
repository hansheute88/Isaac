from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from decision_trace import DecisionTrace, TracePhase
from scripts.isaac_30day_run import (
    append_event,
    backup,
    init_run,
    runtime_trace_stats,
    verify_journal,
    verify_backup,
    sha256_file,
    load_state,
    atomic_json,
)


class TestIsaac30DayRunEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.run_dir = self.base / "run"
        self.backup_dir = self.base / "backup"

    def tearDown(self):
        self.temp.cleanup()

    def test_initialization_creates_valid_hash_chain_without_starting_official_clock(self):
        init_run(self.run_dir, "a" * 40, self.backup_dir)
        state = json.loads((self.run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["phase"], "PREFLIGHT")
        self.assertIsNone(state["official_started_at_utc"])
        self.assertTrue(verify_journal(self.run_dir)["valid"])

    def test_event_chain_detects_tampering(self):
        init_run(self.run_dir, "a" * 40, self.backup_dir)
        append_event(self.run_dir, "heartbeat", {"pid_alive": True})
        self.assertTrue(verify_journal(self.run_dir)["valid"])
        path = self.run_dir / "events.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        item = json.loads(lines[-1])
        item["payload"]["pid_alive"] = False
        lines[-1] = json.dumps(item)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(verify_journal(self.run_dir)["valid"])

    def test_backup_is_outside_run_directory_and_contains_hash_manifest(self):
        init_run(self.run_dir, "b" * 40, self.backup_dir)
        report = backup(self.run_dir, self.backup_dir)
        copied = self.backup_dir / "run"
        self.assertTrue((copied / "backup-manifest.json").exists())
        self.assertEqual(report["files"]["events.jsonl"], __import__("hashlib").sha256((copied / "events.jsonl").read_bytes()).hexdigest())

    def test_backup_rejects_overlapping_target(self):
        init_run(self.run_dir, "c" * 40, self.backup_dir)
        with self.assertRaises(ValueError):
            backup(self.run_dir, self.base)

    def test_runtime_trace_persistence_is_opt_in_and_redacts_sensitive_fields(self):
        trace_path = self.run_dir / "runtime-trace.jsonl"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with patch.dict(os.environ, {"ISAAC_AUTONOMY_TRACE_PATH": str(trace_path)}):
            trace = DecisionTrace()
            trace.add(TracePhase.GOVERNANCE, "authorization_decision", {"action_id": "a1", "authorization_event_id": "auth-event-1", "authorization": {"authorized": True, "token": "do-not-store"}, "api_key": "do-not-store"})
        row = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(row["event"], "authorization_decision")
        self.assertEqual(row["data"]["api_key"], "[REDACTED]")
        self.assertEqual(row["data"]["authorization_event_id"], "auth-event-1")
        self.assertTrue(row["data"]["authorization"]["authorized"])
        self.assertEqual(row["data"]["authorization"]["token"], "[REDACTED]")
        self.assertEqual(runtime_trace_stats(self.run_dir)["entries"], 1)

    def test_backup_manifest_is_bound_to_journal(self):
        init_run(self.run_dir, "d" * 40, self.backup_dir)
        report = backup(self.run_dir, self.backup_dir)
        manifest = self.backup_dir / "run" / "backup-manifest.json"
        append_event(self.run_dir, "backup_completed", {
            "files": report["files"],
            "manifest_sha256": sha256_file(manifest),
        })
        state = load_state(self.run_dir)
        from datetime import datetime, timezone
        state["last_backup_at_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_json(self.run_dir / "run-state.json", state)
        self.assertTrue(verify_backup(self.run_dir, load_state(self.run_dir))["valid"])

    def test_trace_persistence_disabled_by_default(self):
        trace_path = self.run_dir / "runtime-trace.jsonl"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with patch.dict(os.environ, {}, clear=True):
            DecisionTrace().add(TracePhase.EXECUTION, "tool_execution", {"action_id": "a2"})
        self.assertFalse(trace_path.exists())


if __name__ == "__main__":
    unittest.main()
