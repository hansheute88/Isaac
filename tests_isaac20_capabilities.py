from __future__ import annotations

import unittest

from isaac_capabilities import (
    Capability,
    CapabilityRequest,
    RWXPolicy,
    RWXRegistry,
    capability_from_legacy_action,
    evaluate_with_audit,
)


class TestIsaac20Capabilities(unittest.TestCase):
    def test_default_is_implicit_deny(self):
        decision = RWXRegistry().evaluate(
            CapabilityRequest("filesystem:/workspace", Capability.WRITE)
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_source, "implicit-deny")

    def test_explicit_read_write_without_execute(self):
        registry = RWXRegistry()
        registry.set_policy(
            RWXPolicy(
                resource="filesystem:/workspace",
                read=True,
                write=True,
                execute=False,
                source="test",
            )
        )
        self.assertTrue(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "read")
            ).allowed
        )
        self.assertTrue(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "write")
            ).allowed
        )
        self.assertFalse(
            registry.evaluate(
                CapabilityRequest("filesystem:/workspace", "execute")
            ).allowed
        )

    def test_decision_contains_audit_relevant_evidence(self):
        registry = RWXRegistry()
        registry.set_policy(
            RWXPolicy("tool:browser", execute=True, source="owner-policy", version=3)
        )
        decision = registry.evaluate(
            CapabilityRequest(
                "tool:browser",
                Capability.EXECUTE,
                principal="task:123",
                reason="open requested page",
                task_id="123",
            )
        )
        data = decision.as_dict()
        self.assertTrue(data["allowed"])
        self.assertEqual(data["policy_source"], "owner-policy")
        self.assertEqual(data["policy_version"], 3)
        self.assertEqual(data["task_id"], "123")

    def test_evaluate_with_audit_returns_same_decision(self):
        registry = RWXRegistry()
        registry.set_policy(RWXPolicy("tool:browser", execute=True, source="test"))
        decision = evaluate_with_audit(
            registry,
            CapabilityRequest("tool:browser", "execute", task_id="audit-test"),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.task_id, "audit-test")

    def test_legacy_mapping_is_additive(self):
        self.assertEqual(capability_from_legacy_action("file_read"), Capability.READ)
        self.assertEqual(capability_from_legacy_action("file_write"), Capability.WRITE)
        self.assertEqual(capability_from_legacy_action("system_command"), Capability.EXECUTE)


if __name__ == "__main__":
    unittest.main()
