from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from diva_protocol import (
    DIVAProtocol,
    DIVAEvent,
    ProvenanceChain,
    ProvenanceStatus,
    ModulatorSystem,
    ConnectionMap,
)
from memory import Memory, EpistemicClass
from decision_trace import DecisionTrace


class TestDIVAProtocol(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp_dir.name) / "test_diva_state.json"
        self.memory = Memory()
        self.diva = DIVAProtocol(state_path=self.state_path, memory=self.memory)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_step_1_2_provenance_and_trigger(self):
        # 1. Complete provenance -> should NOT trigger DIVA
        prov_complete = ProvenanceChain(status=ProvenanceStatus.COMPLETE, confidence=1.0)
        evt1 = self.diva.evaluate_and_trigger("Known fact", prov_complete, 0.8)
        self.assertIsNone(evt1)

        # 2. Low behavioral relevance -> should NOT trigger DIVA
        prov_unknown = ProvenanceChain(status=ProvenanceStatus.UNKNOWN, confidence=0.1)
        evt2 = self.diva.evaluate_and_trigger("Uncertain fact", prov_unknown, 0.1)
        self.assertIsNone(evt2)

        # 3. Incomplete provenance & high relevance -> SHOULD trigger DIVA
        evt3 = self.diva.evaluate_and_trigger("Critical unverified fact", prov_unknown, 0.9)
        self.assertIsNotNone(evt3)
        self.assertTrue(evt3.event_id.startswith("diva_"))
        self.assertIn(evt3.event_id, self.diva.active_events)

    def test_step_3_memory_coupling(self):
        prov = ProvenanceChain(status=ProvenanceStatus.PARTIAL, confidence=0.4)
        evt = self.diva.evaluate_and_trigger("Ambiguous API endpoint", prov, 0.85)
        self.assertIsNotNone(evt)

        # Check epistemic memory entry creation
        ep_entry = self.memory.get_epistemic_memory(f"diva:{evt.event_id}")
        self.assertIsNotNone(ep_entry)
        self.assertEqual(ep_entry.epistemic_class, EpistemicClass.UNCERTAINTY_EVENT)
        self.assertIn("Ambiguous API endpoint", ep_entry.value)

    def test_step_4_connection_map(self):
        cm = ConnectionMap()
        cm.add_node("n1", "event", {"info": "test1"})
        cm.add_node("n2", "memory", {"info": "test2"})
        cm.add_edge("n1", "n2", weight=0.5)

        self.assertIn("n1->n2", cm.edges)
        self.assertEqual(cm.edges["n1->n2"], 0.5)

        cm.boost_connections("n1", boost_factor=0.3)
        self.assertAlmostEqual(cm.edges["n1->n2"], 0.8)

        associated = cm.get_associated_nodes("n1")
        self.assertIn("n2", associated)

    def test_step_5_modulators_and_persistence(self):
        mod = ModulatorSystem()
        self.assertEqual(mod.uncertainty_arousal, 0.0)

        mod.raise_for_diva(uncertainty_score=0.9, behavioral_relevance=0.8)
        self.assertGreater(mod.uncertainty_arousal, 0.0)
        self.assertGreater(mod.urgency_modifier, 0.0)
        self.assertGreater(mod.memory_bias_strength, 0.0)

        prev_arousal = mod.uncertainty_arousal
        mod.decay(turns=1, accelerated=False)
        self.assertLess(mod.uncertainty_arousal, prev_arousal)

    def test_step_6_7_resolution_and_decay(self):
        prov = ProvenanceChain(status=ProvenanceStatus.UNKNOWN)
        evt = self.diva.evaluate_and_trigger("Uncertain DB port", prov, 0.9)
        self.assertIsNotNone(evt)

        arousal_before = self.diva.modulators.uncertainty_arousal
        resolved = self.diva.resolve_event(evt.event_id, reason="User confirmed port 5432")
        self.assertTrue(resolved)

        self.assertNotIn(evt.event_id, self.diva.active_events)
        self.assertIn(evt.event_id, self.diva.resolved_events)
        self.assertLess(self.diva.modulators.uncertainty_arousal, arousal_before)

    def test_step_8_observability_and_metrics(self):
        dt = DecisionTrace()
        prov = ProvenanceChain(status=ProvenanceStatus.PARTIAL, confidence=0.3)
        evt = self.diva.evaluate_and_trigger("Observability info", prov, 0.9, decision_trace=dt)

        self.assertEqual(len(dt.entries), 1)
        self.assertEqual(dt.entries[0].event, "diva_event_triggered")

        self.diva.resolve_event(evt.event_id, "Verified by tool", decision_trace=dt)
        self.assertEqual(len(dt.entries), 2)
        self.assertEqual(dt.entries[1].event, "diva_event_resolved")

        metrics = self.diva.get_metrics()
        self.assertIn("active_events_count", metrics)
        self.assertIn("resolved_events_count", metrics)
        self.assertIn("modulator_values", metrics)




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
from config import IsaacConfig
from self_model import SelfModel
import tempfile
from pathlib import Path



class TestDivaDecayProtocol(unittest.TestCase):

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
        val = exponential_decay(0.8, elapsed_seconds=1800.0, half_life_seconds=1800.0)
        self.assertAlmostEqual(val, 0.4, places=4)
        self.assertEqual(exponential_decay(0.8, elapsed_seconds=0.0, half_life_seconds=1800.0), 0.8)

    def test_logarithmic_decay(self):
        val1 = logarithmic_decay(0.8, elapsed_seconds=600.0, k=0.35, offset=1.0)
        val2 = logarithmic_decay(0.8, elapsed_seconds=3600.0, k=0.35, offset=1.0)
        self.assertGreater(0.8, val1)
        self.assertGreater(val1, val2)

    def test_linear_decay(self):
        val = linear_decay(0.8, elapsed_seconds=1200.0, total_decay_seconds=2400.0)
        self.assertAlmostEqual(val, 0.4, places=4)

    def test_turn_decay(self):
        val = turn_decay(0.8, rate=0.08, dt_turns=1.0, factor=1.0)
        self.assertAlmostEqual(val, 0.72, places=4)

    def test_decay_modulators_modes(self):
        now = time.time()
        mods = {
            "uncertainty_arousal": 0.8,
            "urgency_modifier": 0.7,
            "memory_bias_strength": 0.6,
            "last_update_ts": now - 900.0,
            "active_diva_events": ["evt_1"],
        }

        decayed_exp = decay_modulators(dict(mods), decay_type="exponential", now=now)
        self.assertLess(decayed_exp["uncertainty_arousal"], 0.8)
        self.assertLess(decayed_exp["urgency_modifier"], 0.7)

        decayed_log = decay_modulators(dict(mods), decay_type="logarithmic", now=now)
        self.assertLess(decayed_log["uncertainty_arousal"], 0.8)

        decayed_lin = decay_modulators(dict(mods), decay_type="linear", now=now)
        self.assertLess(decayed_lin["uncertainty_arousal"], 0.8)

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

        updated = cfg.update_runtime_settings({"diva_enabled": False, "diva_decay_type": "logarithmic"})
        self.assertIn("diva_enabled", updated["changed"])
        self.assertIn("diva_decay_type", updated["changed"])
        self.assertFalse(cfg.diva.enabled)
        self.assertEqual(cfg.diva.decay_type, "logarithmic")

        cfg.update_runtime_settings({"diva_enabled": True, "diva_decay_type": "exponential"})


if __name__ == "__main__":
    unittest.main()