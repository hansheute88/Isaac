from __future__ import annotations

import json
import unittest

from benchmarks.isaac20_metrics import (
    DEFAULT_WEIGHTS,
    measure_e1_evidence,
    run_e2_metrics,
)


class TestIsaac20E2Metrics(unittest.TestCase):
    def test_metrics_are_normalized_and_machine_readable(self):
        report = run_e2_metrics(repetitions=3)
        encoded = json.dumps(report)
        decoded = json.loads(encoded)

        self.assertEqual(decoded["schema_version"], "isaac20-iti-v1")
        self.assertTrue(decoded["experimental"])
        self.assertEqual(set(decoded["dimensions"]), {"T", "C", "G", "S", "R"})
        self.assertTrue(all(0.0 <= value <= 1.0 for value in decoded["dimensions"].values()))
        self.assertAlmostEqual(sum(decoded["weights"].values()), 1.0)
        self.assertGreaterEqual(decoded["iti_score"], 0.0)
        self.assertLessEqual(decoded["iti_score"], 1.0)
        self.assertEqual(decoded["raw_measurements"]["run_count"], 3)
        self.assertTrue(decoded["raw_measurements"]["all_runs_passed"])

    def test_current_e1_evidence_scores_complete_control_chain(self):
        from benchmarks.isaac20_fault_injection import run_e1_benchmark

        report = measure_e1_evidence(run_e1_benchmark())
        self.assertEqual(report.dimensions, {
            "T": 1.0,
            "C": 1.0,
            "G": 1.0,
            "S": 1.0,
            "R": 1.0,
        })
        self.assertAlmostEqual(report.iti_score, 1.0)
        self.assertEqual(report.weights, DEFAULT_WEIGHTS)

    def test_custom_weights_are_normalized_and_applied(self):
        from benchmarks.isaac20_fault_injection import run_e1_benchmark

        report = measure_e1_evidence(run_e1_benchmark())
        # With complete evidence all valid weightings still produce 1.0.
        self.assertEqual(report.iti_score, 1.0)

    def test_invalid_weight_keys_are_rejected(self):
        from benchmarks.isaac20_fault_injection import run_e1_benchmark

        with self.assertRaises(ValueError):
            measure_e1_evidence(run_e1_benchmark(), repetitions=0)


if __name__ == "__main__":
    unittest.main()
