"""Tests: key-file discovery, import rules, browser creds, key reachability."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import key_health
import secrets_bootstrap as sb


class TestEnvKeyImportRules(unittest.TestCase):
    def test_provider_and_runtime_keys_are_importable(self):
        for key in (
            "OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY_ALT",
            "GROQ_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "RENDER_API_KEY",
            "COGNEE_API_KEY",
            "COGNEE_BASE_URL",
            "OPENCODE_API_KEY",
            "SENTRY_DSN",
            "BROWSER_GOOGLE_COM_PASSWORD",
            "ACTIVE_PROVIDER",
        ):
            self.assertTrue(sb.is_importable_env_key(key), key)

    def test_unrelated_keys_are_ignored(self):
        for key in ("", "SOME_RANDOM_VALUE", "BAD KEY", "note"):
            self.assertFalse(sb.is_importable_env_key(key), key)


class TestEnvFileDiscovery(unittest.TestCase):
    def test_discovery_reads_dotenv_and_data_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = root / "data"
            backup = data / "cli_auth_backup"
            backup.mkdir(parents=True)
            (root / ".env").write_text("OPENROUTER_API_KEY=from-dotenv\n", encoding="utf-8")
            (data / "isaac_active_keys.env").write_text(
                "# generated export\nGROQ_API_KEY=gsk_from_file\n", encoding="utf-8"
            )
            (backup / "all_cli_api_keys.env").write_text(
                "OPENCODE_API_KEY=sk-from-backup\n", encoding="utf-8"
            )
            with patch.object(sb, "ROOT", root), patch.object(sb, "DATA_DIR", data), patch.object(
                sb, "DOTENV", root / ".env"
            ), patch.object(sb, "LOCAL_DOTENV", root / ".env.local"), patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OPENROUTER_API_KEY", None)
                os.environ.pop("GROQ_API_KEY", None)
                os.environ.pop("OPENCODE_API_KEY", None)

                found = {p.name for p in sb.discover_env_files()}
                self.assertIn(".env", found)
                self.assertIn("isaac_active_keys.env", found)
                self.assertIn("all_cli_api_keys.env", found)

                stats = sb.load_secret_files_into_environ()
                self.assertEqual(os.environ.get("GROQ_API_KEY"), "gsk_from_file")
                self.assertEqual(os.environ.get("OPENROUTER_API_KEY"), "from-dotenv")
                self.assertEqual(os.environ.get("OPENCODE_API_KEY"), "sk-from-backup")
                self.assertGreaterEqual(stats["files"], 3)
                self.assertGreaterEqual(stats["applied"], 3)

    def test_explicit_secret_files_win(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            explicit = root / "custom.env"
            explicit.write_text("GROQ_API_KEY=gsk_explicit\n", encoding="utf-8")
            with patch.object(sb, "ROOT", root), patch.object(sb, "DATA_DIR", root / "data"), patch.object(
                sb, "DOTENV", root / ".env"
            ), patch.object(sb, "LOCAL_DOTENV", root / ".env.local"), patch.dict(
                os.environ, {"ISAAC_SECRET_FILES": str(explicit)}, clear=False
            ):
                os.environ.pop("GROQ_API_KEY", None)
                self.assertIn(explicit, sb.discover_env_files())
                sb.load_secret_files_into_environ()
                self.assertEqual(os.environ.get("GROQ_API_KEY"), "gsk_explicit")

    def test_process_env_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".env").write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
            with patch.object(sb, "ROOT", root), patch.object(sb, "DATA_DIR", root / "data"), patch.object(
                sb, "DOTENV", root / ".env"
            ), patch.object(sb, "LOCAL_DOTENV", root / ".env.local"), patch.dict(
                os.environ, {"GROQ_API_KEY": "from-process"}, clear=False
            ):
                sb.load_secret_files_into_environ()
                self.assertEqual(os.environ.get("GROQ_API_KEY"), "from-process")


class TestBrowserCredsImport(unittest.TestCase):
    def test_triples_build_entries(self):
        env = {
            "BROWSER_GOOGLE_COM_DOMAIN": "google.com",
            "BROWSER_GOOGLE_COM_USERNAME": "owner@example.com",
            "BROWSER_GOOGLE_COM_PASSWORD": "unit-test-pw",
            "BROWSER_GOOGLE_COM_LOGIN_URL": "https://accounts.example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            entries = sb.browser_creds_from_env()
        self.assertIn("google.com", entries)
        self.assertEqual(entries["google.com"]["username"], "owner@example.com")
        self.assertEqual(entries["google.com"]["login_url"], "https://accounts.example.com")

    def test_json_document_is_imported(self):
        payload = {
            "aistudio.google.com": {
                "domain": "aistudio.google.com",
                "login_url": "https://accounts.example.com",
                "username": "owner@example.com",
                "password": "unit-test-pw",
            }
        }
        with patch.dict(
            os.environ, {"BROWSER_CREDS_JSON_PLAINTEXT": json.dumps(payload)}, clear=False
        ):
            entries = sb.browser_creds_from_env()
        self.assertIn("aistudio.google.com", entries)

    def test_import_keeps_existing_and_writes_0600(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "browser_creds.json"
            target.write_text(
                json.dumps({"google.com": {"username": "old", "password": "old"}}),
                encoding="utf-8",
            )
            env = {
                "BROWSER_GOOGLE_COM_DOMAIN": "google.com",
                "BROWSER_GOOGLE_COM_PASSWORD": "new-pw",
            }
            with patch.dict(os.environ, env, clear=False):
                first = sb.import_browser_creds(target)
                self.assertNotIn("google.com", first["imported"])
                self.assertIn("google.com", first["skipped"])

                second = sb.import_browser_creds(target, overwrite=True)
                self.assertIn("google.com", second["imported"])

            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["google.com"]["password"], "new-pw")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


class TestKeyHealth(unittest.TestCase):
    def test_mask_secret_never_returns_full_value(self):
        masked = key_health.mask_secret("sk-abcdefghijklmnop")
        self.assertNotIn("abcdefghijklmnop", masked)
        self.assertTrue(masked.startswith("sk-a"))
        self.assertEqual(key_health.mask_secret(""), "")

    def test_missing_key_is_reported_without_network(self):
        probe = key_health.Probe("unit", ("ISAAC_TEST_MISSING_KEY",), "https://example.invalid", key_health._bearer)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ISAAC_TEST_MISSING_KEY", None)
            with patch.object(key_health, "_http_get") as http_get:
                row = key_health.probe_provider(probe)
        http_get.assert_not_called()
        self.assertEqual(row["status"], key_health.MISSING)
        self.assertIsNone(row["env_key"])

    def test_status_classification(self):
        self.assertEqual(key_health._classify(200, "")[0], key_health.OK)
        self.assertEqual(key_health._classify(401, "")[0], key_health.UNAUTHORIZED)
        self.assertEqual(key_health._classify(403, "error code: 1010")[0], key_health.BLOCKED)
        self.assertEqual(key_health._classify(429, "")[0], key_health.BLOCKED)
        self.assertEqual(key_health._classify(500, "")[0], key_health.ERROR)

    def test_probe_ok_and_rejection(self):
        probe = key_health.Probe("unit", ("ISAAC_TEST_KEY",), "https://example.invalid", key_health._bearer)
        with patch.dict(os.environ, {"ISAAC_TEST_KEY": "unit-secret-value"}, clear=False):
            with patch.object(key_health, "_http_get", return_value=(200, "{}", None)):
                ok_row = key_health.probe_provider(probe)
            with patch.object(key_health, "_http_get", return_value=(401, "", None)):
                bad_row = key_health.probe_provider(probe)
        self.assertEqual(ok_row["status"], key_health.OK)
        self.assertEqual(bad_row["status"], key_health.UNAUTHORIZED)
        self.assertNotIn("unit-secret-value", json.dumps(ok_row))
        self.assertNotIn("unit-secret-value", json.dumps(bad_row))

    def test_unreachable_provider_is_soft_failure(self):
        probe = key_health.Probe("unit", ("ISAAC_TEST_KEY",), "https://example.invalid", key_health._bearer)
        with patch.dict(os.environ, {"ISAAC_TEST_KEY": "unit-secret-value"}, clear=False):
            with patch.object(key_health, "_http_get", return_value=(0, "", "URLError: timeout")):
                row = key_health.probe_provider(probe)
        self.assertEqual(row["status"], key_health.UNREACHABLE)

    def test_report_contains_no_secret_values(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_unit_secret_value"}, clear=False):
            with patch.object(key_health, "_http_get", return_value=(200, "{}", None)):
                report = key_health.run_key_health(timeout=2)
        blob = json.dumps(report)
        self.assertNotIn("gsk_unit_secret_value", blob)
        self.assertGreaterEqual(report["checked"], len(key_health.PROBES))
        self.assertIn("providers", report)
        self.assertTrue(key_health.format_table(report).startswith("Isaac Key-Health"))


if __name__ == "__main__":
    unittest.main()
