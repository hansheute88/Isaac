from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from isaac_30day_evidence import append_event, evaluate_gates, iso_utc, read_events, verify_chain, _unauthorized_execution_count, _pid_alive
from isaac_interest_derivation import build_interest_derivation
from isaac_learning_causality import build_learning_record


class TestIsaac30DayEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_pid_liveness_check_is_non_destructive_and_rejects_invalid_pid(self):
        self.assertTrue(_pid_alive(os.getpid()))
        self.assertFalse(_pid_alive(0))
        self.assertFalse(_pid_alive(-1))

    def test_hash_chain_detects_tampering(self):
        append_event(self.root, "health_sample", {"healthy": True})
        append_event(self.root, "autonomy_cycle_started", {"cycle_id": "real-cycle"}, source="isaac_runtime")
        records = read_events(self.root)
        self.assertTrue(verify_chain(records)["valid"])
        records[0]["payload"]["healthy"] = False
        self.assertFalse(verify_chain(records)["valid"])

    def test_24_hour_gate_requires_elapsed_time_and_health_evidence(self):
        start_dt = datetime.now(timezone.utc)
        start = iso_utc(start_dt)
        append_event(self.root, "health_sample", {"healthy": True}, event_time=start)
        state = {
            "run_id": "test-run",
            "started_at_utc": start,
            "interval_seconds": 60,
            "previous_sample_gap_seconds": None,
            "gates": {},
        }
        records = read_events(self.root)
        before = evaluate_gates(state, records, now=start_dt + timedelta(hours=23))
        self.assertFalse(before["gates"]["PREFLIGHT_24H"]["passed"])
        after = evaluate_gates(state, records, now=start_dt + timedelta(hours=24))
        self.assertTrue(after["gates"]["PREFLIGHT_24H"]["passed"])

    def test_72_hour_gate_requires_real_cycle_learning_and_interest_events(self):
        start_dt = datetime.now(timezone.utc) - timedelta(hours=73)
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
        learning_payload = build_learning_record(
            learning_id="l-1", research_id="r-1", goal_id="g-1", subgoal_id="sg-1",
            source_cycle_id="c-1", pre_state={"quality": 0.4}, research_evidence=["source-1"],
            post_state={"quality": 0.7}, measurable_delta={"quality_delta": 0.3},
            affected_decision_ids=["decision-2"], evidence_event_ids=["event-2"],
        ).to_dict()
        interest_base = {
            "owner_goal_id": "g-1", "subgoal_id": "sg-1", "observation_research_id": "r-1",
            "new_information": "Grounded new information", "inference": "Goal-related inference",
            "interest_proposal": "Bounded follow-up topic", "alignment_check": {"aligned": True},
            "scope_check": {"bounded": True}, "risk_check": {"acceptable": True},
            "authorization": {"authorized": True},
        }
        interest_payloads = [
            build_interest_derivation(interest_id="i-1", **interest_base).to_dict(),
            build_interest_derivation(interest_id="i-2", **interest_base).to_dict(),
        ]
        timestamp = iso_utc(start_dt + timedelta(hours=73))
        for kind, source, payload in [
            ("health_sample", "supervisor", {"healthy": True}),
            ("autonomy_cycle_started", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_authorization_observed", "isaac_runtime", {"cycle_id": "c-1", "allowed": True}),
            ("autonomy_execution_observed", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_evaluation_recorded", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_learning_recorded", "isaac_runtime", learning_payload),
            ("research_cycle_completed", "isaac_runtime", learning_payload),
            ("interest_derivation_recorded", "isaac_runtime", interest_payloads[0]),
            ("interest_derivation_recorded", "isaac_runtime", interest_payloads[1]),
            ("proof_audit_readiness", "isaac_runtime", {
                "coverage_complete": True,
                "surfaces": ["executor_tools", "owner_actions", "browser_missions", "mcp_tools", "state_store_writes", "filesystem_state"],
            }),
        ]:
            append_event(self.root, kind, payload, source=source, event_time=timestamp)
        result = evaluate_gates(state, read_events(self.root), now=start_dt + timedelta(hours=73))
        self.assertTrue(result["gates"]["AUTONOMY_72H"]["passed"])
        self.assertTrue(result["audit_coverage_complete"])

        # The same otherwise-valid evidence must fail closed without readiness.
        no_audit_root = self.root / "without-audit-readiness"
        for event in read_events(self.root):
            if event.get("event_type") == "proof_audit_readiness":
                continue
            append_event(
                no_audit_root,
                event["event_type"],
                event.get("payload") or {},
                source=event.get("source", "supervisor"),
                event_time=event.get("timestamp_utc"),
            )
        no_audit_result = evaluate_gates(
            state, read_events(no_audit_root), now=start_dt + timedelta(hours=73)
        )
        self.assertFalse(no_audit_result["gates"]["AUTONOMY_72H"]["passed"])
        self.assertFalse(no_audit_result["audit_coverage_complete"])

        missing_root = self.root / "without-learning"
        for kind, source, payload in [
            ("health_sample", "supervisor", {"healthy": True}),
            ("autonomy_cycle_started", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_authorization_observed", "isaac_runtime", {"cycle_id": "c-1", "allowed": True}),
            ("autonomy_execution_observed", "isaac_runtime", {"cycle_id": "c-1"}),
            ("autonomy_evaluation_recorded", "isaac_runtime", {"cycle_id": "c-1"}),
            ("interest_derivation_recorded", "isaac_runtime", interest_payloads[0]),
            ("interest_derivation_recorded", "isaac_runtime", interest_payloads[1]),
            ("proof_audit_readiness", "isaac_runtime", {
                "coverage_complete": True,
                "surfaces": ["executor_tools", "owner_actions", "browser_missions", "mcp_tools", "state_store_writes", "filesystem_state"],
            }),
        ]:
            append_event(missing_root, kind, payload, source=source, event_time=timestamp)
        result = evaluate_gates(state, read_events(missing_root), now=start_dt + timedelta(hours=73))
        self.assertFalse(result["gates"]["AUTONOMY_72H"]["passed"])

    def test_execution_without_matching_allow_is_counted_as_unauthorized(self):
        denied_then_invoked = [
            {"event_type": "tool_authorization_decision", "payload": {"action_id": "a-1", "allowed": False}},
            {"event_type": "tool_execution_result", "payload": {"action_id": "a-1", "invoked": True}},
        ]
        denied_without_invocation = [
            {"event_type": "tool_authorization_decision", "payload": {"action_id": "a-2", "allowed": False}},
            {"event_type": "tool_execution_result", "payload": {"action_id": "a-2", "invoked": False}},
        ]
        allowed_then_invoked = [
            {"event_type": "tool_authorization_decision", "payload": {"action_id": "a-3", "allowed": True}},
            {"event_type": "tool_execution_result", "payload": {"action_id": "a-3", "invoked": True}},
        ]
        self.assertEqual(_unauthorized_execution_count(denied_then_invoked), 1)
        self.assertEqual(_unauthorized_execution_count(denied_without_invocation), 0)
        self.assertEqual(_unauthorized_execution_count(allowed_then_invoked), 0)

    def test_no_event_chain_can_pass_if_a_record_is_modified(self):
        append_event(self.root, "health_sample", {"healthy": True})
        raw = (self.root / "events.jsonl").read_text(encoding="utf-8")
        row = json.loads(raw)
        row["payload"]["healthy"] = False
        (self.root / "events.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.assertFalse(verify_chain(read_events(self.root))["valid"])


if __name__ == "__main__":
    unittest.main()
