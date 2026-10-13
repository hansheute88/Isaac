"""Tests for Isaac 2.0 F1 governance evidence package."""
from __future__ import annotations

import unittest

from benchmarks.isaac20_ablation import run_e3_benchmark
from benchmarks.isaac20_fault_injection import run_e1_benchmark
from benchmarks.isaac20_governance import (
    LEGAL_DISCLAIMER,
    SCHEMA_VERSION,
    build_governance_evidence,
    verify_governance_evidence,
)
from benchmarks.isaac20_metrics import run_e2_metrics


class GovernanceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e1 = run_e1_benchmark()
        cls.e2 = run_e2_metrics(repetitions=2)
        cls.e3 = run_e3_benchmark()

    def test_schema_and_required_evidence(self):
        package = build_governance_evidence(
            e1_report=self.e1,
            e2_report=self.e2,
            e3_report=self.e3,
            audit_events=[{"event_id": "audit-1", "typ": "action"}],
            decision_trace={"trace_id": "trace-1"},
            capability_decisions=[{"audit_event_id": "audit-1", "allowed": True}],
            config_snapshot={"feature_flags": {"guardrails": True}},
        )
        self.assertEqual(package["schema_version"], SCHEMA_VERSION)
        self.assertIn("legal_disclaimer", package)
        self.assertEqual(package["legal_disclaimer"], LEGAL_DISCLAIMER)
        self.assertEqual(set(package["benchmarks"]), {"e1", "e2", "e3"})
        self.assertIn("runtime_evidence", package)
        self.assertEqual(package["integrity"]["algorithm"], "sha256")

    def test_integrity_verifies_and_tampering_fails(self):
        package = build_governance_evidence(
            e1_report=self.e1, e2_report=self.e2, e3_report=self.e3
        )
        self.assertTrue(verify_governance_evidence(package))
        package["benchmarks"]["e1"]["passed"] = False
        self.assertFalse(verify_governance_evidence(package))

    def test_e1_e2_e3_prerequisites_are_preserved(self):
        package = build_governance_evidence(
            e1_report=self.e1, e2_report=self.e2, e3_report=self.e3
        )
        self.assertTrue(package["benchmarks"]["e1"]["passed"])
        self.assertTrue(package["benchmarks"]["e2"]["experimental"])
        self.assertTrue(package["benchmarks"]["e3"]["passed"])
        self.assertEqual(
            package["benchmarks"]["e3"]["claim_scope"],
            "contract_level_control_contribution",
        )


if __name__ == "__main__":
    unittest.main()
