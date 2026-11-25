"""Provider key reachability checks for Isaac.

Answers one question per configured provider: does the stored key still work
right now? Every probe is a single cheap authenticated GET against the
provider's own API. Keys are never printed or logged - only a masked hint.

Entry points:
    run_key_health()          -> machine-readable report dict
    format_table(report)      -> short human-readable table
    maybe_log_key_health()    -> optional startup check (ISAAC_KEY_HEALTH_ON_START=1)

CLI: ``python3 scripts/check_key_health.py``
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger("Isaac.KeyHealth")

DATA_DIR = Path(__file__).parent / "data"
REPORT_PATH = DATA_DIR / "key_health.json"
DEFAULT_TIMEOUT_S = 8.0
USER_AGENT = "isaac-key-health/1.0"

OK = "ok"
MISSING = "missing"
UNAUTHORIZED = "unauthorized"
BLOCKED = "blocked"
UNREACHABLE = "unreachable"
ERROR = "error"
FORMAT_OK = "format_ok"


def _bearer(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def _goog(key: str) -> dict[str, str]:
    return {"x-goog-api-key": key}


def _anthropic(key: str) -> dict[str, str]:
    return {"x-api-key": key, "anthropic-version": "2023-06-01"}


def _github(key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@dataclass(frozen=True)
class Probe:
    provider: str
    env_keys: tuple[str, ...]
    url: str
    headers: Callable[[str], dict[str, str]]
    label: str = ""


PROBES: tuple[Probe, ...] = (
    Probe("openrouter", ("OPENROUTER_API_KEY", "OPENROUTER_API_KEY_ALT"),
          "https://openrouter.ai/api/v1/key", _bearer, "OpenRouter"),
    Probe("groq", ("GROQ_API_KEY",),
          "https://api.groq.com/openai/v1/models", _bearer, "Groq"),
    Probe("gemini", ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
          "https://generativelanguage.googleapis.com/v1beta/models", _goog, "Gemini"),
    Probe("openai", ("OPENAI_API_KEY", "OPENAI_API_KEY_SVCACCT"),
          "https://api.openai.com/v1/models", _bearer, "OpenAI"),
    Probe("anthropic", ("ANTHROPIC_API_KEY",),
          "https://api.anthropic.com/v1/models", _anthropic, "Anthropic"),
    Probe("xai", ("XAI_API_KEY",),
          "https://api.x.ai/v1/models", _bearer, "xAI"),
    Probe("github", ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN_GLINKASTEFFEN075_BIT"),
          "https://api.github.com/user", _github, "GitHub"),
    Probe("render", ("RENDER_API_KEY",),
          "https://api.render.com/v1/owners?limit=1", _bearer, "Render"),
)

# Keys without a cheap public "who am I" endpoint: presence/format only.
FORMAT_ONLY: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("sentry", ("SENTRY_DSN",), "dsn"),
    ("cognee", ("COGNEE_API_KEY",), "len64"),
    ("opencode", ("OPENCODE_API_KEY",), "prefix"),
)


def mask_secret(value: str) -> str:
    """Short, non-reversible hint for a secret (never the full value)."""
    v = (value or "").strip()
    if not v:
        return ""
    if len(v) <= 8:
        return f"*** (len={len(v)})"
    return f"{v[:4]}… (len={len(v)})"


def _first_env(keys: tuple[str, ...]) -> tuple[Optional[str], str]:
    for key in keys:
        value = (os.getenv(key) or "").strip()
        if value:
            return key, value
    return None, ""


def _http_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, str, Optional[str]]:
    """Single GET. Returns (status, body_snippet, error_text)."""
    request = urllib.request.Request(url, headers={**headers, "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(400).decode("utf-8", "replace")
            return int(getattr(response, "status", 200) or 200), body, None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(400).decode("utf-8", "replace")
        except Exception:
            body = ""
        return int(exc.code or 0), body, None
    except Exception as exc:
        return 0, "", f"{type(exc).__name__}: {exc}"[:160]


def _classify(status: int, body: str) -> tuple[str, str]:
    low = (body or "").lower()
    if status in (200, 201):
        return OK, "key accepted"
    if status in (401, 403):
        if "cloudflare" in low or '"1010"' in low or "1010" in low[:40]:
            return BLOCKED, "IP/Cloudflare block, key not judged"
        if "quota" in low or "insufficient" in low or "billing" in low:
            return BLOCKED, "quota/billing limit, key itself may be fine"
        return UNAUTHORIZED, "key rejected (401/403)"
    if status == 429:
        return BLOCKED, "rate limited (429)"
    if status == 0:
        return UNREACHABLE, "no response"
    return ERROR, f"HTTP {status}"


def probe_provider(probe: Probe, *, timeout: float = DEFAULT_TIMEOUT_S) -> dict[str, Any]:
    env_key, value = _first_env(probe.env_keys)
    name = probe.label or probe.provider
    if not env_key:
        return {
            "provider": name,
            "env_key": None,
            "status": MISSING,
            "http_status": None,
            "detail": "no key configured",
            "hint": "",
            "ms": 0,
        }
    started = time.monotonic()
    status, body, error = _http_get(probe.url, probe.headers(value), timeout)
    ms = round((time.monotonic() - started) * 1000, 1)
    if error:
        verdict, detail = UNREACHABLE, error
    else:
        verdict, detail = _classify(status, body)
    return {
        "provider": name,
        "env_key": env_key,
        "status": verdict,
        "http_status": status or None,
        "detail": detail,
        "hint": mask_secret(value),
        "ms": ms,
    }


def _format_only(name: str, env_keys: tuple[str, ...], rule: str) -> dict[str, Any]:
    env_key, value = _first_env(env_keys)
    label = name.capitalize()
    if not env_key:
        return {
            "provider": label,
            "env_key": None,
            "status": MISSING,
            "http_status": None,
            "detail": "no key configured",
            "hint": "",
            "ms": 0,
        }
    ok = True
    if rule == "dsn":
        ok = value.startswith(("http://", "https://")) and "@" in value
        detail = "DSN looks valid (not posted)"
    elif rule == "len64":
        ok = len(value) >= 32
        detail = "key present, no public check endpoint"
    else:
        ok = bool(value)
        detail = "key present, not live-checked"
    return {
        "provider": label,
        "env_key": env_key,
        "status": FORMAT_OK if ok else ERROR,
        "http_status": None,
        "detail": detail,
        "hint": mask_secret(value),
        "ms": 0,
    }


def run_key_health(*, timeout: Optional[float] = None) -> dict[str, Any]:
    """Probe every configured provider. Returns a JSON-safe report."""
    try:
        budget = float(timeout if timeout is not None else os.getenv("ISAAC_KEY_HEALTH_TIMEOUT_S", DEFAULT_TIMEOUT_S))
    except (TypeError, ValueError):
        budget = DEFAULT_TIMEOUT_S
    budget = max(1.0, min(budget, 30.0))

    rows: list[dict[str, Any]] = []
    for probe in PROBES:
        try:
            rows.append(probe_provider(probe, timeout=budget))
        except Exception as exc:  # a probe must never break the report
            rows.append({
                "provider": probe.label or probe.provider,
                "env_key": None,
                "status": ERROR,
                "http_status": None,
                "detail": f"probe error: {type(exc).__name__}",
                "hint": "",
                "ms": 0,
            })
    for name, env_keys, rule in FORMAT_ONLY:
        rows.append(_format_only(name, env_keys, rule))

    bad = [r for r in rows if r["status"] in {UNAUTHORIZED, ERROR, UNREACHABLE}]
    blocked = [r for r in rows if r["status"] == BLOCKED]
    present = [r for r in rows if r["status"] != MISSING]
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": not bad,
        "checked": len(rows),
        "present": len(present),
        "ok_count": sum(1 for r in rows if r["status"] in {OK, FORMAT_OK}),
        "failed": len(bad),
        "blocked": len(blocked),
        "providers": rows,
    }


def write_report(report: dict[str, Any], path: Optional[Path] = None) -> Optional[Path]:
    target = path or REPORT_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        try:
            target.chmod(0o600)
        except OSError:
            pass
        return target
    except OSError as exc:
        log.debug("key health report not written: %s", exc)
        return None


def format_table(report: dict[str, Any]) -> str:
    lines = [
        f"Isaac Key-Health {report.get('generated_at', '')}".rstrip(),
        f"{'Provider':<12} {'Status':<12} {'HTTP':<5} Detail",
        "-" * 68,
    ]
    for row in report.get("providers", []):
        http_status = row.get("http_status")
        lines.append(
            f"{str(row.get('provider')):<12} {str(row.get('status')):<12} "
            f"{str(http_status or '-'):<5} {row.get('detail', '')[:40]}"
        )
    lines.append("-" * 68)
    lines.append(
        f"ok={report.get('ok_count')} failed={report.get('failed')} "
        f"blocked={report.get('blocked')} missing="
        f"{report.get('checked', 0) - report.get('present', 0)}"
    )
    return "\n".join(lines)


def _flag_enabled(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default) or default).strip().lower() in {"1", "true", "yes", "on"}


def maybe_log_key_health() -> Optional[dict[str, Any]]:
    """Startup hook: run once when ISAAC_KEY_HEALTH_ON_START=1."""
    if not _flag_enabled("ISAAC_KEY_HEALTH_ON_START"):
        return None
    report = run_key_health()
    write_report(report)
    for row in report.get("providers", []):
        if row.get("status") in {OK, FORMAT_OK}:
            log.info("Key %s: %s", row.get("provider"), row.get("status"))
        else:
            log.warning(
                "Key %s: %s (%s)", row.get("provider"), row.get("status"), row.get("detail")
            )
    return report


if __name__ == "__main__":  # pragma: no cover - manual helper
    print(format_table(run_key_health()))
