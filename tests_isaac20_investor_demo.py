"""Contract tests for the Isaac 2.0 H1 investor demo."""
from __future__ import annotations

import unittest

from benchmarks.isaac20_investor_demo import (
    DEMO_SCHEMA,
    build_demo_contract,
    render_demo_summary,
)


class InvestorDemoTests(unittest.TestCase):
    def evidence(self):
        return {
            "unauthorized": {"audit_event_id": "audit-1", "allowed": False},
            "fault": {"fault_injected": True, "causal_evidence": {"event_id": "error-1"}},
            "recovery": {"verified": True},
            "governance": {
                "schema_version": "isaac20-governance-evidence-v1",
                "integrity": {"evidence_hash": "abc123"},
            },
        }

    def test_demo_contract_passes_only_when_all_stages_have_evidence(self):
        contract = build_demo_contract(**self.evidence())
        self.assertEqual(contract["schema_version"], DEMO_SCHEMA)
        self.assertTrue(contract["passed"])
        self.assertEqual(
            [step["name"] for step in contract["steps"]],
            ["observe", "authorize", "execute", "explain", "recover"],
        )

    def test_missing_recovery_verification_fails_demo(self):
        evidence = self.evidence()
        evidence["recovery"] = {"verified": False}
        contract = build_demo_contract(**evidence)
        self.assertFalse(contract["passed"])
        self.assertEqual(contract["steps"][-1]["status"], "FAIL")

    def test_summary_is_presentation_ready(self):
        summary = render_demo_summary(build_demo_contract(**self.evidence()))
        self.assertIn("Observe → Authorize → Execute → Explain → Recover", summary)
        self.assertIn("Result: PASS", summary)
        self.assertIn("RECOVER", summary)


if __name__ == "__main__":
    unittest.main()
