from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
