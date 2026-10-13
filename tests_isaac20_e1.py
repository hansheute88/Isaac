from __future__ import annotations

import json
import unittest

from benchmarks.isaac20_fault_injection import run_e1_benchmark, run_fault_injection


class TestIsaac20E1FaultInjection(unittest.TestCase):
    def test_verified_recovery_completes_full_d3_lifecycle(self):
        result = run_fault_injection(
            scenario="verified",
            verification_probe=lambda: True,
        )
        self.assertTrue(result.passed)
        self.assertEqual(
            result.lifecycle,
            [
                "fault_injected",
                "failure_observed",
                "intervention",
                "quarantined",
                "recovery",
                "verification",
                "verified",
                "released",
            ],
        )
        self.assertEqual(result.evidence["final_state"], "verified")
        self.assertFalse(result.evidence["provider_quarantined"])
        self.assertTrue(result.evidence["recovery_event_id"])
        self.assertTrue(result.evidence["verification_event_id"])

    def test_failed_verification_retains_quarantine(self):
        result = run_fault_injection(
            scenario="failed",
            verification_probe=lambda: False,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.evidence["final_state"], "failed")
        self.assertTrue(result.evidence["provider_quarantined"])
        self.assertIn("quarantine_retained", result.lifecycle)
        self.assertNotIn("released", result.lifecycle)

    def test_suite_is_machine_readable_and_contains_both_outcomes(self):
        report = run_e1_benchmark()
        encoded = json.dumps(report)
        decoded = json.loads(encoded)

        self.assertEqual(decoded["schema_version"], "isaac20-e1-suite-v1")
        self.assertEqual(decoded["benchmark"], "fault_injection_d3_lifecycle")
        self.assertTrue(decoded["passed"])
        self.assertEqual(len(decoded["scenarios"]), 2)
        self.assertEqual(
            {scenario["evidence"]["final_state"] for scenario in decoded["scenarios"]},
            {"verified", "failed"},
        )


if __name__ == "__main__":
    unittest.main()
