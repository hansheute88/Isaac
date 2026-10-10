from __future__ import annotations

import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from isaac_30day_evidence import (
    append_event,
    evaluate_gates,
    iso_utc,
    read_events,
    verify_chain,
)


class TestIsaac30DayEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_hash_chain_detects_tampering(self):
        append_event(self.root, "health_sample", {"healthy": True})
        append_event(self.root, "autonomy_cycle_started", {"cycle_id": "real-cycle"}, source="isaac_runtime")
        records = read_events(self.root)
        self.assertTrue(verify_chain(records)["valid"])
        records[0]["payload"]["healthy"] = False
        self.assertFalse(verify_chain(records)["valid"])

    def test_24_hour_gate_requires_elapsed_time_and_health_evidence(self):
        now = iso_utc()
        start = iso_utc()
        state = {
            "run_id": "test-run",
            "started_at_utc": start,
            "interval_seconds": 60,
            "previous_sample_gap_seconds": None,
            "gates": {},
        }
        records = [{
            "timestamp_utc": now,
            "event_type": "health_sample",
            "source": "supervisor",
            "payload": {"healthy": True},
        }]
        before = evaluate_gates(state, records, now=__import__("datetime").datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(hours=23))
        self.assertFalse(before["gates"]["PREFLIGHT_24H"]["passed"])
        after = evaluate_gates(state, records, now=__import__("datetime").datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(hours=24))
        self.assertTrue(after["gates"]["PREFLIGHT_24H"]["passed"])

    def test_72_hour_gate_requires_real_cycle_learning_and_interest_events(self):
        start_dt = __import__("datetime").datetime.now(__import__("datetime").timezone.utc) - timedelta(hours=73)
        start = iso_utc(start_dt)
        state = {
            "run_id": "test-run",
            "started_at_utc": start,
            "interval_seconds": 60,
            "previous_sample_gap_seconds": None,
            "gates": {
                "PREFLIGHT_24H": {"passed": True},
                "STABILITY_48H": {"passed": True},
            },
        }
        records = []
        for kind, source, payload in [
            ("health_sample", "supervisor", {"healthy": True}),
            ("autonomy_cycle_started", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_authorization_observed", "isaac_runtime", {"cycle_id": "c-1", "allowed": True}),
            ("autonomy_execution_observed", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_evaluation_recorded", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_learning_recorded", "isaac_runtime", {"learning_id": "l-1"}),
            ("interest_derivation_recorded", "isaac_runtime", {"interest_id": "i-1"}),
        ]:
            records.append({
                "timestamp_utc": iso_utc(start_dt + timedelta(hours=73)),
                "event_type": kind,
                "source": source,
                "payload": payload,
            })
        result = evaluate_gates(state, records, now=start_dt + timedelta(hours=73))
        self.assertTrue(result["gates"]["AUTONOMY_72H"]["passed"])
        records = [r for r in records if r["event_type"] != "autonomy_learning_recorded"]
        result = evaluate_gates(state, records, now=start_dt + timedelta(hours=73))
        self.assertFalse(result["gates"]["AUTONOMY_72H"]["passed"])

    def test_no_event_chain_can_pass_if_a_record_is_modified(self):
        append_event(self.root, "health_sample", {"healthy": True})
        raw = (self.root / "events.jsonl").read_text(encoding="utf-8")
        row = json.loads(raw)
        row["payload"]["healthy"] = False
        (self.root / "events.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.assertFalse(verify_chain(read_events(self.root))["valid"])


if __name__ == "__main__":
    unittest.main()
