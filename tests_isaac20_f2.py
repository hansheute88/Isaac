"""Tests for Isaac 2.0 F2 governance provenance."""
from __future__ import annotations

import copy
import unittest

from benchmarks.isaac20_ablation import run_e3_benchmark
from benchmarks.isaac20_fault_injection import run_e1_benchmark
from benchmarks.isaac20_governance import build_governance_evidence
from benchmarks.isaac20_governance_f2 import (
    SCHEMA_VERSION,
    build_reproducibility_manifest,
    verify_reproducibility_manifest,
)
from benchmarks.isaac20_metrics import run_e2_metrics


class GovernanceProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = build_governance_evidence(
            e1_report=run_e1_benchmark(),
            e2_report=run_e2_metrics(repetitions=2),
            e3_report=run_e3_benchmark(),
            config_snapshot={"feature_flags": {"guardrails": True}},
        )

    def test_manifest_binds_revision_and_f1_integrity(self):
        manifest = build_reproducibility_manifest(
            evidence_package=self.package,
            source_revision="18ff242",
            workflow_run_id="12345",
            workflow_name="Isaac 2.0 Validation",
        )
        self.assertEqual(manifest["schema_version"], SCHEMA_VERSION)
        self.assertEqual(manifest["source_revision"], "18ff242")
        self.assertTrue(manifest["evidence"]["evidence_hash"])
        self.assertTrue(verify_reproducibility_manifest(
            manifest, evidence_package=self.package
        ))

    def test_manifest_tampering_fails(self):
        manifest = build_reproducibility_manifest(
            evidence_package=self.package,
            source_revision="abc123",
        )
        tampered = copy.deepcopy(manifest)
        tampered["source_revision"] = "attacker-revision"
        self.assertFalse(verify_reproducibility_manifest(
            tampered, evidence_package=self.package
        ))

    def test_wrong_evidence_package_fails(self):
        manifest = build_reproducibility_manifest(
            evidence_package=self.package,
            source_revision="abc123",
        )
        other = copy.deepcopy(self.package)
        other["benchmarks"]["e1"]["passed"] = False
        self.assertFalse(verify_reproducibility_manifest(
            manifest, evidence_package=other
        ))

    def test_benchmark_contracts_are_bound(self):
        manifest = build_reproducibility_manifest(
            evidence_package=self.package,
            source_revision="abc123",
        )
        self.assertEqual(
            set(manifest["benchmark_contracts"]),
            {"e1", "e2", "e3"},
        )
        for contract in manifest["benchmark_contracts"].values():
            self.assertIn("schema_version", contract)
            self.assertIn("passed", contract)


if __name__ == "__main__":
    unittest.main()
