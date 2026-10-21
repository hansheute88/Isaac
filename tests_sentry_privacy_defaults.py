"""Regression tests for opt-in Sentry telemetry privacy defaults."""
import os
import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import isaac_sentry


class FakeSpan:
    def __init__(self):
        self.data = {}
        self.tags = {}

    def set_data(self, key, value):
        self.data[key] = value

    def set_tag(self, key, value):
        self.tags[key] = value


class SentryPrivacyTests(unittest.TestCase):
    def setUp(self):
        isaac_sentry._initialized = False
        isaac_sentry._include_prompts = False
        self.span = FakeSpan()
        self.init_options = {}
        self.user_calls = []
        fake_sdk = types.ModuleType("sentry_sdk")
        fake_sdk.init = lambda **kw: self.init_options.update(kw)
        fake_sdk.set_user = lambda data: self.user_calls.append(data)
        fake_sdk.set_tag = lambda *args, **kw: None
        fake_sdk.set_context = lambda *args, **kw: None

        @contextmanager
        def transaction(**kwargs):
            yield self.span

        fake_sdk.start_transaction = transaction
        self.fake_sdk = fake_sdk

    def tearDown(self):
        isaac_sentry._initialized = False
        isaac_sentry._include_prompts = False

    def test_default_does_not_send_prompt_or_owner(self):
        with patch.dict(os.environ, {"SENTRY_DSN": "https://public@example.invalid/1"}, clear=True), \
             patch.dict(sys.modules, {"sentry_sdk": self.fake_sdk}), \
             patch.object(isaac_sentry, "_build_integrations", return_value=[]), \
             patch.object(isaac_sentry, "set_conversation_id"):
            self.assertTrue(isaac_sentry.init_sentry())
            self.assertFalse(self.init_options["send_default_pii"])
            self.assertEqual(self.init_options["traces_sample_rate"], 0.05)
            self.assertEqual(self.init_options["profile_session_sample_rate"], 0.0)
            self.assertNotIn("enable_logs", self.init_options)
            self.assertEqual(self.user_calls, [])
            with isaac_sentry.request_transaction(user_input="PRIVATE_PROMPT"):
                pass
            self.assertNotIn("input_preview", self.span.tags)
            self.assertEqual(self.span.data["isaac.input_chars"], 14)

    def test_explicit_opt_in_enables_sensitive_capture(self):
        with patch.dict(os.environ, {
            "SENTRY_DSN": "https://public@example.invalid/1",
            "SENTRY_INCLUDE_PROMPTS": "1",
        }, clear=True), patch.dict(sys.modules, {"sentry_sdk": self.fake_sdk}), \
             patch.object(isaac_sentry, "_build_integrations", return_value=[]), \
             patch.object(isaac_sentry, "set_conversation_id"):
            self.assertTrue(isaac_sentry.init_sentry())
            self.assertTrue(self.init_options["send_default_pii"])
            self.assertEqual(len(self.user_calls), 1)


if __name__ == "__main__":
    unittest.main()
