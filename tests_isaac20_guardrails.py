from __future__ import annotations

import asyncio
import os
import time
import unittest
from unittest.mock import patch

from isaac_guardrails import (
    GuardrailController,
    GuardrailState,
    InterventionType,
)
from watchdog import ProviderBlacklist, ProviderStats


class FakeBlacklist:
    def __init__(self):
        self.quarantined = []
        self.verified = []

    def quarantine(self, provider, *, reason="", source_event_id=""):
        self.quarantined.append((provider, reason, source_event_id))

    def verify_quarantine(self, provider):
        self.verified.append(provider)
        return True


class TestGuardrailRuntimeRecovery(unittest.TestCase):
    """D4: Quarantäne endet nur über explizite, probe-verifizierte Recovery."""

    def _quarantined_blacklist(self):
        blacklist = object.__new__(ProviderBlacklist)
        blacklist._stats = {"groq": ProviderStats("groq")}
        blacklist.quarantine(
            "groq", reason="safety_critical_failure", source_event_id="evt-quarantine"
        )
        blacklist._stats["groq"].guardrail_quarantined_at = 0.0  # Cooldown überspringen
        return blacklist

    def test_auto_recovery_releases_after_successful_probe(self):
        from watchdog import TaskWatchdog

        blacklist = self._quarantined_blacklist()
        controller = GuardrailController(blacklist)

        with patch.dict(os.environ, {"ISAAC_GUARDRAIL_AUTO_RECOVERY": "1"}):
            outcomes = asyncio.run(
                TaskWatchdog()._maybe_recover_quarantined_providers(
                    blacklist=blacklist,
                    controller=controller,
                    probe_resolver=lambda provider: (lambda: True),
                )
            )

        self.assertEqual(outcomes, {"groq": GuardrailState.VERIFIED.value})
        self.assertFalse(blacklist.is_quarantined("groq"))

    def test_auto_recovery_failed_probe_keeps_quarantine(self):
        from watchdog import TaskWatchdog

        blacklist = self._quarantined_blacklist()
        controller = GuardrailController(blacklist)

        with patch.dict(os.environ, {"ISAAC_GUARDRAIL_AUTO_RECOVERY": "1"}):
            outcomes = asyncio.run(
                TaskWatchdog()._maybe_recover_quarantined_providers(
                    blacklist=blacklist,
                    controller=controller,
                    probe_resolver=lambda provider: (lambda: False),
                )
            )

        self.assertEqual(outcomes, {"groq": GuardrailState.FAILED.value})
        self.assertTrue(blacklist.is_quarantined("groq"))

    def test_auto_recovery_is_opt_in(self):
        from watchdog import TaskWatchdog

        blacklist = self._quarantined_blacklist()

        with patch.dict(os.environ, {"ISAAC_GUARDRAIL_AUTO_RECOVERY": "0"}):
            outcomes = asyncio.run(
                TaskWatchdog()._maybe_recover_quarantined_providers(
                    blacklist=blacklist,
                    controller=GuardrailController(blacklist),
                    probe_resolver=lambda provider: (lambda: True),
                )
            )

        self.assertEqual(outcomes, {})
        self.assertTrue(blacklist.is_quarantined("groq"))

    def test_cooldown_prevents_immediate_recovery_attempt(self):
        from watchdog import TaskWatchdog

        blacklist = self._quarantined_blacklist()
        blacklist._stats["groq"].guardrail_quarantined_at = time.monotonic()

        with patch.dict(os.environ, {"ISAAC_GUARDRAIL_AUTO_RECOVERY": "1"}):
            outcomes = asyncio.run(
                TaskWatchdog()._maybe_recover_quarantined_providers(
                    blacklist=blacklist,
                    controller=GuardrailController(blacklist),
                    probe_resolver=lambda provider: (lambda: True),
                )
            )

        self.assertEqual(outcomes, {})
        self.assertTrue(blacklist.is_quarantined("groq"))


class TestIsaac20Guardrails(unittest.TestCase):
    def test_safety_critical_failure_quarantines_existing_provider_authority(self):
        fake = FakeBlacklist()
        controller = GuardrailController(fake)

        decision = controller.intervene_provider(
            provider="test-provider",
            failed_event_id="failure-1",
            error="unsafe provider behavior",
            safety_critical=True,
            task_id="task-1",
        )

        self.assertEqual(decision.state, GuardrailState.QUARANTINED)
        self.assertEqual(decision.intervention, InterventionType.QUARANTINE)
        self.assertEqual(fake.quarantined[0][0], "test-provider")
        self.assertEqual(fake.quarantined[0][2], "failure-1")

    def test_quarantine_requires_explicit_verification_for_release(self):
        stats = ProviderStats("test-provider")
        blacklist = object.__new__(ProviderBlacklist)
        blacklist._stats = {"test-provider": stats}

        blacklist.quarantine(
            "test-provider",
            reason="safety_critical_failure",
            source_event_id="failure-2",
        )
        self.assertTrue(blacklist.is_quarantined("test-provider"))
        self.assertFalse(blacklist.is_available("test-provider"))
        self.assertEqual(blacklist.ranked_providers(), [])

        blacklist.verify_quarantine("test-provider")
        self.assertFalse(blacklist.is_quarantined("test-provider"))
        self.assertTrue(blacklist.is_available("test-provider"))
        self.assertEqual(blacklist.ranked_providers(), ["test-provider"])

    def test_verification_transitions_to_verified(self):
        fake = FakeBlacklist()
        controller = GuardrailController(fake)

        intervention = controller.intervene_provider(
            provider="test-provider",
            failed_event_id="failure-3",
            error="fault",
            safety_critical=True,
        )
        event_id = controller.last_intervention_event_id("provider:test-provider")
        self.assertTrue(event_id)

        verified = controller.verify_provider(
            provider="test-provider",
            intervention_event_id=event_id,
            verified=True,
            reason="safe verification passed",
        )

        self.assertEqual(intervention.state, GuardrailState.QUARANTINED)
        self.assertEqual(verified.state, GuardrailState.VERIFIED)
        self.assertEqual(fake.verified, ["test-provider"])

    def test_noncritical_failure_enters_degraded_recovery_path(self):
        fake = FakeBlacklist()
        controller = GuardrailController(fake)

        decision = controller.intervene_provider(
            provider="test-provider",
            failed_event_id="failure-4",
            error="temporary timeout",
            safety_critical=False,
        )
        self.assertEqual(decision.state, GuardrailState.DEGRADED)
        self.assertEqual(decision.intervention, InterventionType.RECOVER)
        self.assertEqual(fake.quarantined, [])

        recovery_event = controller.begin_recovery(
            resource="provider:test-provider",
            source_event_id="failure-4",
            reason="fallback provider selected",
        )
        self.assertTrue(recovery_event)
        self.assertEqual(
            controller.state("provider:test-provider"),
            GuardrailState.RECOVERING,
        )

    def test_recovery_requires_controlled_probe_before_release(self):
        fake = FakeBlacklist()
        controller = GuardrailController(fake)
        controller.intervene_provider(
            provider="test-provider",
            failed_event_id="failure-d3-success",
            error="critical fault",
            safety_critical=True,
        )
        refs = {}
        recovered = []
        decision = controller.recover_and_verify_provider(
            provider="test-provider",
            source_event_id="failure-d3-success",
            reason="safe provider reset",
            recovery_action=lambda: recovered.append("reset"),
            verification_probe=lambda: True,
            task_id="task-d3-success",
            causal_refs=refs,
        )
        self.assertEqual(recovered, ["reset"])
        self.assertEqual(decision.state, GuardrailState.VERIFIED)
        self.assertEqual(fake.verified, ["test-provider"])
        self.assertTrue(refs["guardrail_recovery_event_id"])
        self.assertTrue(refs["guardrail_verification_event_id"])

    def test_failed_probe_keeps_quarantine_and_enters_failed_state(self):
        fake = FakeBlacklist()
        controller = GuardrailController(fake)
        controller.intervene_provider(
            provider="test-provider",
            failed_event_id="failure-d3-fail",
            error="critical fault",
            safety_critical=True,
        )
        refs = {}
        decision = controller.recover_and_verify_provider(
            provider="test-provider",
            source_event_id="failure-d3-fail",
            reason="safe provider reset",
            recovery_action=lambda: None,
            verification_probe=lambda: False,
            task_id="task-d3-fail",
            causal_refs=refs,
        )
        self.assertEqual(decision.state, GuardrailState.FAILED)
        self.assertEqual(fake.verified, [])
        self.assertTrue(refs["guardrail_recovery_event_id"])
        self.assertTrue(refs["guardrail_verification_event_id"])

    def test_watchdog_high_risk_hang_routes_to_quarantine(self):
        from executor import Task, TaskType
        from watchdog import TaskWatchdog

        class FakeController:
            def __init__(self):
                self.calls = []

            def intervene_provider(self, **kwargs):
                self.calls.append(kwargs)
                from isaac_guardrails import GuardrailDecision
                return GuardrailDecision(
                    GuardrailState.QUARANTINED,
                    InterventionType.QUARANTINE,
                    "safety_critical_failure",
                    kwargs.get("failed_event_id", ""),
                    True,
                )

        class FakeExecutor:
            def __init__(self):
                self._running = set()

            async def submit(self, task):
                return True

            def resume_task(self, task_id):
                return False

        fake_controller = FakeController()
        task = Task(
            id="watchdog-critical",
            typ=TaskType.CODE,
            prompt="critical task",
            beschreibung="watchdog guardrail",
            provider="unsafe-provider",
            risk_level="critical",
        )
        watchdog = TaskWatchdog()
        watchdog.set_executor(FakeExecutor())

        with patch("memory.get_memory") as get_memory,              patch("task_checkpoint.is_resumable_state", return_value=False),              patch("isaac_guardrails.get_guardrail_controller", return_value=fake_controller):
            get_memory.return_value.get_latest_checkpoint.return_value = None
            import asyncio
            asyncio.run(watchdog._handle_hang(task, 301.0))

        self.assertEqual(len(fake_controller.calls), 1)
        self.assertEqual(fake_controller.calls[0]["provider"], "unsafe-provider")
        self.assertTrue(fake_controller.calls[0]["safety_critical"])
        self.assertEqual(task.causal_refs.get("guardrail_source_event_id") != "", True)


if __name__ == "__main__":
    unittest.main()
