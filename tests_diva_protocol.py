from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from diva_protocol import (
    clamp_modulator,
    create_initial_diva_modulators,
    decay_modulators,
    exponential_decay,
    linear_decay,
    logarithmic_decay,
    on_diva_resolved,
    raise_modulators,
    turn_decay,
    check_cognitive_loss_trigger,
)
from config import IsaacConfig, DivaConfig
from self_model import SelfModel


class TestDivaProtocol(unittest.TestCase):

    def test_initial_structure(self):
        mods = create_initial_diva_modulators()
        self.assertEqual(mods["uncertainty_arousal"], 0.0)
        self.assertEqual(mods["urgency_modifier"], 0.0)
        self.assertEqual(mods["memory_bias_strength"], 0.0)
        self.assertIsInstance(mods["last_update_ts"], float)
        self.assertEqual(mods["active_diva_events"], [])

    def test_clamp_modulator(self):
        self.assertEqual(clamp_modulator(-0.5), 0.0)
        self.assertEqual(clamp_modulator(0.5), 0.5)
        self.assertEqual(clamp_modulator(1.5), 1.0)

    def test_raise_modulators(self):
        mods = create_initial_diva_modulators()
        now = time.time()
        # uncertainty=0.8, relevance=0.5 -> strength = 0.4
        # arousal += 0.4 * 0.4 = 0.16
        # urgency += 0.3 * 0.4 = 0.12
        # memory_bias += 0.35 * 0.4 = 0.14
        updated = raise_modulators(
            mods,
            uncertainty=0.8,
            relevance=0.5,
            event_id="evt_001",
            now=now,
        )
        self.assertAlmostEqual(updated["uncertainty_arousal"], 0.16, places=4)
        self.assertAlmostEqual(updated["urgency_modifier"], 0.12, places=4)
        self.assertAlmostEqual(updated["memory_bias_strength"], 0.14, places=4)
        self.assertIn("evt_001", updated["active_diva_events"])
        self.assertEqual(updated["last_update_ts"], now)

    def test_exponential_decay(self):
        # After 1 half life (1800s), 0.8 should decay to 0.4
        val = exponential_decay(0.8, elapsed_seconds=1800.0, half_life_seconds=1800.0)
        self.assertAlmostEqual(val, 0.4, places=4)

        # Elapsed = 0 -> no decay
        self.assertEqual(exponential_decay(0.8, elapsed_seconds=0.0, half_life_seconds=1800.0), 0.8)

    def test_logarithmic_decay(self):
        # Logarithmic decay should decrease value over time
        val1 = logarithmic_decay(0.8, elapsed_seconds=600.0, k=0.35, offset=1.0)
        val2 = logarithmic_decay(0.8, elapsed_seconds=3600.0, k=0.35, offset=1.0)
        self.assertGreater(0.8, val1)
        self.assertGreater(val1, val2)

    def test_linear_decay(self):
        # Linear decay: elapsed 1200 / total 2400 -> progress 0.5 -> half value (0.4)
        val = linear_decay(0.8, elapsed_seconds=1200.0, total_decay_seconds=2400.0)
        self.assertAlmostEqual(val, 0.4, places=4)

    def test_turn_decay(self):
        # Turn decay: 0.8 - (0.08 * 1.0 * 1.0) = 0.72
        val = turn_decay(0.8, rate=0.08, dt_turns=1.0, factor=1.0)
        self.assertAlmostEqual(val, 0.72, places=4)

    def test_decay_modulators_modes(self):
        now = time.time()
        mods = {
            "uncertainty_arousal": 0.8,
            "urgency_modifier": 0.7,
            "memory_bias_strength": 0.6,
            "last_update_ts": now - 900.0,  # 15 minutes ago
            "active_diva_events": ["evt_1"],
        }

        # Exponential decay mode
        decayed_exp = decay_modulators(dict(mods), decay_type="exponential", now=now)
        self.assertLess(decayed_exp["uncertainty_arousal"], 0.8)
        self.assertLess(decayed_exp["urgency_modifier"], 0.7)

        # Logarithmic decay mode
        decayed_log = decay_modulators(dict(mods), decay_type="logarithmic", now=now)
        self.assertLess(decayed_log["uncertainty_arousal"], 0.8)

        # Linear decay mode
        decayed_lin = decay_modulators(dict(mods), decay_type="linear", now=now)
        self.assertLess(decayed_lin["uncertainty_arousal"], 0.8)

        # Turn decay mode
        decayed_turn = decay_modulators(dict(mods), decay_type="turn", now=now)
        self.assertEqual(decayed_turn["uncertainty_arousal"], max(0.0, 0.8 - 0.08))

    def test_on_diva_resolved(self):
        now = time.time()
        mods = {
            "uncertainty_arousal": 0.8,
            "urgency_modifier": 0.7,
            "memory_bias_strength": 0.6,
            "last_update_ts": now,
            "active_diva_events": ["evt_001", "evt_002"],
        }
        resolved_mods = on_diva_resolved(mods, event_id="evt_001", now=now)
        self.assertNotIn("evt_001", resolved_mods["active_diva_events"])
        self.assertIn("evt_002", resolved_mods["active_diva_events"])
        # Immediate reduction factor 0.4 -> 0.8 * 0.4 = 0.32
        self.assertAlmostEqual(resolved_mods["uncertainty_arousal"], 0.32, places=4)

    def test_cognitive_loss_trigger(self):
        self.assertTrue(check_cognitive_loss_trigger(2.5, threshold=2.0))
        self.assertFalse(check_cognitive_loss_trigger(1.5, threshold=2.0))

    def test_self_model_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sm_path = Path(tmpdir) / "self_model.json"
            sm = SelfModel(path=sm_path)
            mods = sm.get_diva_modulators()
            self.assertEqual(mods["uncertainty_arousal"], 0.0)

            mods["uncertainty_arousal"] = 0.75
            mods["active_diva_events"] = ["evt_test"]
            sm.save_diva_modulators(mods, audit=True)

            # Re-load from disk
            sm_reloaded = SelfModel(path=sm_path)
            mods_reloaded = sm_reloaded.get_diva_modulators()
            self.assertEqual(mods_reloaded["uncertainty_arousal"], 0.75)
            self.assertEqual(mods_reloaded["active_diva_events"], ["evt_test"])

    def test_config_integration(self):
        cfg = IsaacConfig()
        cfg.update_runtime_settings({"diva_enabled": True, "diva_decay_type": "exponential"})
        self.assertTrue(cfg.diva.enabled)
        self.assertEqual(cfg.diva.decay_type, "exponential")
        self.assertEqual(cfg.diva.resolved_multiplier, 3.0)

        # Test patch runtime settings
        updated = cfg.update_runtime_settings({"diva_enabled": False, "diva_decay_type": "logarithmic"})
        self.assertIn("diva_enabled", updated["changed"])
        self.assertIn("diva_decay_type", updated["changed"])
        self.assertFalse(cfg.diva.enabled)
        self.assertEqual(cfg.diva.decay_type, "logarithmic")

        # Cleanup
        cfg.update_runtime_settings({"diva_enabled": True, "diva_decay_type": "exponential"})


if __name__ == "__main__":
    unittest.main()
