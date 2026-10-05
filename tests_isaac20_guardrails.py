from __future__ import annotations

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
