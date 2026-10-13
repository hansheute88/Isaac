from __future__ import annotations

import json
import unittest

from benchmarks.isaac20_ablation import SCENARIOS, VARIANTS, run_e3_ablation


class TestIsaac20E3Ablation(unittest.TestCase):
    def test_report_is_machine_readable_and_contains_all_variants(self):
        report = run_e3_ablation()
        decoded = json.loads(json.dumps(report))

        self.assertEqual(decoded["schema_version"], "isaac20-e3-ablation-v1")
        self.assertTrue(decoded["experimental"])
        self.assertEqual(decoded["claim_scope"], "contract_level_control_contribution")
        self.assertEqual(
            [row["variant"] for row in decoded["variants"]],
            [variant.name for variant in VARIANTS],
        )
        self.assertEqual(
            set(decoded["variants"][0]["scenario_outcomes"]),
            set(SCENARIOS),
        )

    def test_each_layer_contributes_its_declared_control(self):
        report = run_e3_ablation()
        by_name = {row["variant"]: row for row in report["variants"]}

        self.assertFalse(by_name["baseline"]["scenario_outcomes"]["unauthorized_execution"])
        self.assertTrue(by_name["rwx"]["scenario_outcomes"]["unauthorized_execution"])
        self.assertTrue(by_name["causal"]["scenario_outcomes"]["causal_trace"])
        self.assertTrue(by_name["guardrail"]["scenario_outcomes"]["provider_quarantine"])
        self.assertTrue(by_name["recovery"]["scenario_outcomes"]["verified_recovery"])
        self.assertEqual(by_name["full"]["pass_rate"], 1.0)

    def test_full_variant_is_backed_by_e1_verified_and_failed_outcomes(self):
        report = run_e3_ablation()
        self.assertTrue(report["full_variant_e1_prerequisite"]["passed"])
        self.assertEqual(
            set(report["full_variant_e1_prerequisite"]["terminal_states"]),
            {"verified", "failed"},
        )
        self.assertTrue(all(report["pass_criteria"].values()))


if __name__ == "__main__":
    unittest.main()
