from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import background_loop


class TestBackgroundAutonomyLifecycle(unittest.TestCase):
    def test_lifecycle_events_are_append_only_and_hash_chained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autonomy_lifecycle.jsonl"
            loop = background_loop.BackgroundLoop.__new__(background_loop.BackgroundLoop)
            loop._lifecycle_run_id = "run_test"
            loop._lifecycle_sequence = 0
            loop._lifecycle_prev_hash = "0" * 64

            with patch.object(background_loop, "AUTONOMY_LIFECYCLE_PATH", path):
                loop._record_autonomy_lifecycle("run_started", {"tick_seconds": 30})
                first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
                loop._record_autonomy_lifecycle("heartbeat", {"tick": 1})
                records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(len(records), 2)
            self.assertEqual([item["sequence"] for item in records], [1, 2])
            self.assertEqual(records[1]["previous_hash"], first["event_hash"])
            self.assertEqual(records[0]["event_type"], "run_started")
            for record in records:
                supplied_hash = record.pop("event_hash")
                canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                self.assertEqual(supplied_hash, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_lifecycle_chain_restores_sequence_and_hash_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autonomy_lifecycle.jsonl"
            loop = background_loop.BackgroundLoop.__new__(background_loop.BackgroundLoop)
            loop._lifecycle_sequence = 0
            loop._lifecycle_prev_hash = "0" * 64
            with patch.object(background_loop, "AUTONOMY_LIFECYCLE_PATH", path):
                loop._lifecycle_run_id = "run_first"
                loop._record_autonomy_lifecycle("run_started")
                last = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])

                restarted = background_loop.BackgroundLoop.__new__(background_loop.BackgroundLoop)
                restarted._lifecycle_sequence = 0
                restarted._lifecycle_prev_hash = "0" * 64
                restarted._restore_lifecycle_chain()
                restarted._lifecycle_run_id = "run_second"
                restarted._record_autonomy_lifecycle("run_started")
                records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(restarted._lifecycle_sequence, 2)
            self.assertEqual(records[1]["previous_hash"], last["event_hash"])
            self.assertEqual(records[1]["run_id"], "run_second")


if __name__ == "__main__":
    unittest.main()
