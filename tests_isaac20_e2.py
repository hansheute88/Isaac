from __future__ import annotations

import json
import unittest

from benchmarks.isaac20_metrics import DEFAULT_WEIGHTS, measure_e1_evidence, run_e2_metrics
from benchmarks.isaac20_fault_injection import run_e1_benchmark


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
        self.assertEqual(decoded["raw_measurements"]["stable_runs"], 3)
        self.assertTrue(decoded["raw_measurements"]["all_runs_passed"])

    def test_current_e1_evidence_scores_complete_control_chain(self):
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
        report = measure_e1_evidence(
            run_e1_benchmark(),
            weights={"T": 2, "C": 1, "G": 1, "S": 1, "R": 1},
        )
        self.assertAlmostEqual(report.weights["T"], 2 / 6)
        self.assertAlmostEqual(sum(report.weights.values()), 1.0)
        self.assertEqual(report.iti_score, 1.0)

    def test_invalid_weight_keys_and_values_are_rejected(self):
        report = run_e1_benchmark()
        with self.assertRaises(ValueError):
            measure_e1_evidence(report, weights={"T": 1})
        with self.assertRaises(ValueError):
            measure_e1_evidence(
                report,
                weights={"T": -1, "C": 1, "G": 1, "S": 1, "R": 1},
            )
        with self.assertRaises(ValueError):
            measure_e1_evidence(
                report,
                weights={"T": 0, "C": 0, "G": 0, "S": 0, "R": 0},
            )

    def test_repetitions_must_be_positive(self):
        with self.assertRaises(ValueError):
            measure_e1_evidence(run_e1_benchmark(), repetitions=0)
        with self.assertRaises(ValueError):
            run_e2_metrics(repetitions=0)


if __name__ == "__main__":
    unittest.main()
