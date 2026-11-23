"""
Load secrets from environment + local key files into SecretsStore.

Never commits secrets. Safe for CI (no-op if nothing present).

Sources (priority: existing os.environ wins, then files in this order):
  1. process environment
  2. ISAAC_SECRET_FILES (os.pathsep-separated explicit paths)
  3. .env
  4. .env.local
  5. data/*.env  (e.g. data/isaac_active_keys.env)
  6. data/cli_auth_backup/*.env  (all_cli_api_keys.env, …)

Also mirrors well-known keys into SecretsStore refs for tool auth and can
import browser logins from BROWSER_* env vars into data/browser_creds.json.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("Isaac.SecretsBootstrap")

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
BACKUP_ENV = DATA_DIR / "cli_auth_backup" / "all_cli_api_keys.env"
DOTENV = ROOT / ".env"
LOCAL_DOTENV = ROOT / ".env.local"
BROWSER_CREDS_PATH = DATA_DIR / "browser_creds.json"


# env key → secrets_store ref
SECRET_REFS: dict[str, str] = {
    "GROQ_API_KEY": "provider.groq.api_key",
    "OPENROUTER_API_KEY": "provider.openrouter.api_key",
    "OPENAI_API_KEY": "provider.openai.api_key",
    "GOOGLE_API_KEY": "provider.gemini.api_key",
    "GEMINI_API_KEY": "provider.gemini.api_key",
    "ANTHROPIC_API_KEY": "provider.anthropic.api_key",
    "XAI_API_KEY": "provider.xai.api_key",
    "GITHUB_TOKEN": "github.token",
    "GH_TOKEN": "github.token",
    "GITHUB_TOKEN_GLINKASTEFFEN075_BIT": "github.token",
    "COPILOT_GITHUB_TOKEN": "github.copilot_token",
    "SENTRY_DSN": "sentry.dsn",
    "COGNEE_API_KEY": "memory.cognee.api_key",
    "COGNEE_BASE_URL": "memory.cognee.base_url",
    "RENDER_API_KEY": "render.api_key",
    "RENDER_SERVICE_ID": "render.service_id",
    "OPENCODE_API_KEY": "provider.opencode.api_key",
    "OPENROUTER_API_KEY_ALT": "provider.openrouter.api_key_alt",
}

# Keys that may be applied INTO os.environ from backup if missing
IMPORT_ENV_KEYS = frozenset(SECRET_REFS.keys()) | {
    "ACTIVE_PROVIDER",
    "GROQ_MODEL",
    "OPENROUTER_MODEL",
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "SENTRY_TRACES_SAMPLE_RATE",
    "SENTRY_ENVIRONMENT",
    "SENTRY_RELEASE",
    "SENTRY_INCLUDE_PROMPTS",
    "ISAAC_GROK_AGENT_ENABLED",
    "ISAAC_COPILOT_AGENT_ENABLED",
    "ISAAC_COPILOT_AGENT_ALWAYS_APPROVE",
    "ISAAC_COPILOT_CLOUD_REPO",
    "ISAAC_AGENT_AUTO_SELECT",
    "ISAAC_REMOTE_BRIDGE_ENABLED",
    "ISAAC_REMOTE_FREE_URL",
    "ISAAC_REMOTE_TIMEOUT",
    "ISAAC_REMOTE_LABEL",
    "ISAAC_OWNER",
    "COPILOT_GITHUB_TOKEN",
}

# Broader import rule so a full key export file works as-is.
IMPORT_ENV_PREFIXES = (
    "ISAAC_",
    "GROQ_",
    "OPENROUTER_",
    "OPENAI_",
    "GOOGLE_",
    "GEMINI_",
    "ANTHROPIC_",
    "XAI_",
    "GITHUB_",
    "GH_",
    "COPILOT_",
    "SENTRY_",
    "COGNEE_",
    "RENDER_",
    "OPENCODE_",
    "BROWSER_",
    "ACTIVE_PROVIDER",
    "OLLAMA_",
    "LOCAL_LLM_",
)
IMPORT_ENV_SUFFIXES = ("_API_KEY", "_TOKEN", "_DSN", "_SECRET", "_PASSWORD")


def is_importable_env_key(key: str) -> bool:
    """True when an env-file key should be applied to os.environ."""
    k = (key or "").strip()
    if not k or not k.replace("_", "").isalnum():
        return False
    if k in IMPORT_ENV_KEYS:
        return True
    if k.endswith(IMPORT_ENV_SUFFIXES):
        return True
    return k.startswith(IMPORT_ENV_PREFIXES)


def discover_env_files() -> list[Path]:
    """Candidate key files, in priority order (first value wins)."""
    files: list[Path] = []

    def _add(path: Path) -> None:
        try:
            if path.is_file() and path not in files:
                files.append(path)
        except OSError:
            pass

    raw_extra = (os.getenv("ISAAC_SECRET_FILES") or "").replace(";", os.pathsep)
    for chunk in raw_extra.split(os.pathsep):
        chunk = chunk.strip()
        if chunk:
            _add(Path(chunk).expanduser())
    _add(DOTENV)
    _add(LOCAL_DOTENV)
    try:
        if DATA_DIR.is_dir():
            for path in sorted(DATA_DIR.glob("*.env")):
                _add(path)
            for path in sorted((DATA_DIR / "cli_auth_backup").glob("*.env")):
                _add(path)
    except OSError:
        pass
    return files


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and v:
                out[k] = v
    except Exception as exc:
        log.debug("parse env file %s: %s", path, exc)
    return out


def load_secret_files_into_environ(*, overwrite: bool = False) -> dict[str, Any]:
    """Load keys from every discovered key file into os.environ.

    A value already present in the process environment wins unless
    ``overwrite=True``. Values are never logged.
    """
    stats: dict[str, Any] = {
        "files": 0,
        "applied": 0,
        "skipped_existing": 0,
        "sources": [],
    }
    for path in discover_env_files():
        data = _parse_env_file(path)
        if not data:
            continue
        stats["files"] += 1
        stats["sources"].append(path.name)
        for k, v in data.items():
            if not is_importable_env_key(k):
                continue
            if not v:
                continue
            if k in os.environ and os.environ.get(k) and not overwrite:
                stats["skipped_existing"] += 1
                continue
            os.environ[k] = v
            stats["applied"] += 1
    return stats


def browser_creds_from_env() -> dict[str, dict[str, Any]]:
    """Build browser_creds entries from BROWSER_* env vars.

    Supports both shapes of the generated export:
      * ``BROWSER_CREDS_JSON_PLAINTEXT`` — the full JSON document
      * ``BROWSER_<HOST>_{DOMAIN,USERNAME,PASSWORD,LOGIN_URL}`` triples
    """
    entries: dict[str, dict[str, Any]] = {}

    raw_json = (os.getenv("BROWSER_CREDS_JSON_PLAINTEXT") or "").strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
        except Exception as exc:
            log.debug("BROWSER_CREDS_JSON_PLAINTEXT not parseable: %s", exc)
            parsed = None
        if isinstance(parsed, dict):
            for domain, payload in parsed.items():
                if not isinstance(payload, dict):
                    continue
                if payload.get("username") or payload.get("password"):
                    entries[str(domain)] = dict(payload)

    for key in sorted(os.environ):
        if not key.startswith("BROWSER_") or not key.endswith("_PASSWORD"):
            continue
        prefix = key[: -len("_PASSWORD")]
        password = (os.getenv(key) or "").strip()
        if not password:
            continue
        username = (os.getenv(f"{prefix}_USERNAME") or "").strip()
        domain = (os.getenv(f"{prefix}_DOMAIN") or "").strip()
        if not domain and username:
            domain = username.split("@")[-1].strip()
        if not domain:
            continue
        login_url = (os.getenv(f"{prefix}_LOGIN_URL") or "").strip()
        entries.setdefault(
            domain,
            {
                "domain": domain,
                "login_url": login_url or f"https://{domain}",
                "username": username,
                "password": password,
                "user_selector": (
                    "input[type='email'], input[name='email'], input[name='username']"
                ),
                "pass_selector": "input[type='password']",
                "submit_selector": "button[type='submit'], input[type='submit']",
                "logged_in_check": "",
                "extra_steps": [],
            },
        )
    return entries


def import_browser_creds(
    path: Path | None = None, *, overwrite: bool = False
) -> dict[str, Any]:
    """Merge BROWSER_* logins into data/browser_creds.json (0600, gitignored).

    Existing entries are kept unless ``overwrite=True``.
    """
    entries = browser_creds_from_env()
    if not entries:
        return {"imported": [], "skipped": [], "written": False}

    target = path or BROWSER_CREDS_PATH
    existing: dict[str, Any] = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except Exception as exc:
            log.debug("browser_creds not parseable, keeping file: %s", exc)
            return {"imported": [], "skipped": sorted(entries), "written": False}

    imported: list[str] = []
    skipped: list[str] = []
    for domain, payload in entries.items():
        if domain in existing and not overwrite:
            skipped.append(domain)
            continue
        existing[domain] = payload
        imported.append(domain)

    if imported:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".tmp")
            tmp.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.chmod(0o600)
            tmp.replace(target)
        except OSError as exc:
            log.warning("browser_creds import failed: %s", exc)
            return {"imported": [], "skipped": skipped, "written": False}
    return {
        "imported": sorted(imported),
        "skipped": sorted(skipped),
        "written": bool(imported),
    }


def sync_environ_to_secrets_store() -> dict[str, Any]:
    """Mirror known env secrets into SecretsStore (values never logged)."""
    from secrets_store import get_secrets_store

    store = get_secrets_store()
    written: list[str] = []
    for env_key, ref in SECRET_REFS.items():
        val = (os.getenv(env_key) or "").strip()
        if not val:
            continue
        # Prefer first non-empty; don't overwrite existing store with empty
        existing = store.get_secret(ref)
        if existing and existing == val:
            continue
        if existing and env_key in {"GH_TOKEN", "GITHUB_TOKEN_GLINKASTEFFEN075_BIT"}:
            # keep primary GITHUB_TOKEN if set
            if (os.getenv("GITHUB_TOKEN") or "").strip():
                continue
        store.set_secret(ref, val, kind="api_key")
        written.append(ref)
    return {"written_refs": written, "count": len(written)}


def resolve_secret(ref_or_env: str, default: str = "") -> str:
    """Resolve secret by store ref or env var name."""
    if not ref_or_env:
        return default
    # env first
    if ref_or_env.isupper() or ref_or_env.replace("_", "").isalnum():
        env_val = (os.getenv(ref_or_env) or "").strip()
        if env_val:
            return env_val
    try:
        from secrets_store import get_secrets_store

        val = get_secrets_store().get_secret(ref_or_env)
        if val:
            return str(val)
    except Exception:
        pass
    # map env name via SECRET_REFS
    ref = SECRET_REFS.get(ref_or_env)
    if ref:
        try:
            from secrets_store import get_secrets_store

            val = get_secrets_store().get_secret(ref)
            if val:
                return str(val)
        except Exception:
            pass
    return default


def bootstrap_secrets(*, overwrite_env: bool = False) -> dict[str, Any]:
    """Full bootstrap: files → environ → secrets store → browser creds."""
    file_stats = load_secret_files_into_environ(overwrite=overwrite_env)
    store_stats = sync_environ_to_secrets_store()

    browser_stats: dict[str, Any] = {"imported": [], "skipped": [], "written": False}
    import_flag = str(os.getenv("ISAAC_IMPORT_BROWSER_CREDS", "1")).strip().lower()
    if import_flag not in {"0", "false", "no", "off"}:
        try:
            browser_stats = import_browser_creds()
        except Exception as exc:
            log.debug("browser creds import skipped: %s", exc)

    result = {
        "ok": True,
        "from_files": file_stats,
        "store": store_stats,
        "browser_creds": browser_stats,
        "github_token_present": bool(resolve_secret("GITHUB_TOKEN") or resolve_secret("GH_TOKEN")),
        "groq_present": bool(resolve_secret("GROQ_API_KEY")),
        "sentry_dsn_present": bool(resolve_secret("SENTRY_DSN")),
        "xai_present": bool(resolve_secret("XAI_API_KEY")),
    }
    log.info(
        "Secrets bootstrap: files=%s applied=%s store_refs=%s browser_creds=%s",
        file_stats.get("files"),
        file_stats.get("applied"),
        store_stats.get("count"),
        len(browser_stats.get("imported") or []),
    )
    return result
