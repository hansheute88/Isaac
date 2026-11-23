"""Contract tests for the Isaac 2.0 H1 investor demo."""
from __future__ import annotations

import unittest

from benchmarks.isaac20_investor_demo import (
    DEMO_SCHEMA,
    build_demo_contract,
    render_demo_summary,
    run_investor_demo,
)


class InvestorDemoTests(unittest.TestCase):
    def evidence(self):
        return {
            "unauthorized": {"audit_event_id": "audit-1", "allowed": False},
            "fault": {
                "fault_injected": True,
                "causal_evidence": {
                    "failure_event_id": "failure-1",
                    "intervention_event_id": "intervention-1",
                },
            },
            "recovery": {"verified": True},
            "governance": {
                "schema_version": "isaac20-governance-evidence-v1",
                "integrity": {"algorithm": "sha256", "evidence_hash": "abc123"},
            },
        }

    def test_demo_contract_passes_only_when_all_stages_have_evidence(self):
        # The fixture is deliberately synthetic; runtime execution is covered
        # by test_real_demo_executes_existing_benchmarks.
        evidence = self.evidence()
        from unittest.mock import patch

        with patch(
            "benchmarks.isaac20_investor_demo.verify_governance_evidence",
            return_value=True,
        ):
            contract = build_demo_contract(**evidence)
        self.assertEqual(contract["schema_version"], DEMO_SCHEMA)
        self.assertTrue(contract["passed"])
        self.assertEqual(
            [step["name"] for step in contract["steps"]],
            ["observe", "authorize", "execute", "explain", "recover"],
        )

    def test_missing_recovery_verification_fails_demo(self):
        evidence = self.evidence()
        evidence["recovery"] = {"verified": False}
        from unittest.mock import patch

        with patch(
            "benchmarks.isaac20_investor_demo.verify_governance_evidence",
            return_value=True,
        ):
            contract = build_demo_contract(**evidence)
        self.assertFalse(contract["passed"])
        self.assertEqual(contract["steps"][-1]["status"], "FAIL")

    def test_summary_is_presentation_ready(self):
        evidence = self.evidence()
        from unittest.mock import patch

        with patch(
            "benchmarks.isaac20_investor_demo.verify_governance_evidence",
            return_value=True,
        ):
            summary = render_demo_summary(build_demo_contract(**evidence))
        self.assertIn("Observe → Authorize → Execute → Explain → Recover", summary)
        self.assertIn("Result: PASS", summary)
        self.assertIn("RECOVER", summary)

    def test_real_demo_executes_existing_benchmarks(self):
        result = run_investor_demo(e2_repetitions=2)
        self.assertTrue(result["demo"]["passed"])
        self.assertTrue(result["benchmarks"]["e1"]["passed"])
        self.assertTrue(result["benchmarks"]["e2"]["experimental"])
        self.assertTrue(result["benchmarks"]["e3"]["passed"])
        self.assertTrue(result["demo"]["governance_evidence"]["integrity_verified"])
        self.assertTrue(result["demo"]["evidence"]["authorization_event_id"])
        self.assertTrue(result["demo"]["evidence"]["failure_event_id"])
        self.assertTrue(result["demo"]["evidence"]["intervention_event_id"])
        self.assertTrue(result["demo"]["evidence"]["recovery_event_id"])
        self.assertTrue(result["demo"]["evidence"]["verification_event_id"])


if __name__ == "__main__":
    unittest.main()
