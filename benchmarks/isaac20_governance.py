"""Isaac 2.0 F1 — governance evidence package.

Builds a machine-readable, integrity-verifiable evidence package from benchmark
reports and supplied runtime evidence. This is an evidence format, not a legal
compliance engine and makes no automatic legal-compliance determination.
"""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from typing import Any, Mapping


SCHEMA_VERSION = "isaac20-governance-evidence-v1"
LEGAL_DISCLAIMER = (
    "This package is an engineering evidence artifact. It does not constitute "
    "legal advice, certification, or an automatic determination of legal or "
    "regulatory compliance. Human/legal review remains required."
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_evidence(
    *,
    audit_events: list[Mapping[str, Any]] | None,
    decision_trace: Mapping[str, Any] | None,
    capability_decisions: list[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    return {
        "audit_events": [dict(item) for item in (audit_events or [])],
        "decision_trace": dict(decision_trace or {}),
        "capability_decisions": [dict(item) for item in (capability_decisions or [])],
    }


def build_governance_evidence(
    *,
    e1_report: Mapping[str, Any],
    e2_report: Mapping[str, Any],
    e3_report: Mapping[str, Any],
    audit_events: list[Mapping[str, Any]] | None = None,
    decision_trace: Mapping[str, Any] | None = None,
    capability_decisions: list[Mapping[str, Any]] | None = None,
    config_snapshot: Mapping[str, Any] | None = None,
    system_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic evidence with a hash over the complete evidence body."""
    body = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "system_identity": dict(system_identity or {
            "python": platform.python_version(),
            "platform": platform.platform(),
        }),
        "config_snapshot": dict(config_snapshot or {}),
        "runtime_evidence": _normalize_evidence(
            audit_events=audit_events,
            decision_trace=decision_trace,
            capability_decisions=capability_decisions,
        ),
        "benchmarks": {
            "e1": dict(e1_report),
            "e2": dict(e2_report),
            "e3": dict(e3_report),
        },
    }
    integrity_payload = dict(body)
    integrity_payload.pop("generated_at", None)
    package_hash = sha256_json(integrity_payload)
    body["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "json-sort-keys-compact-utf8",
        "evidence_hash": package_hash,
    }
    return body


def verify_governance_evidence(package: Mapping[str, Any]) -> bool:
    """Verify the package hash without trusting its stored hash value."""
    integrity = package.get("integrity", {})
    expected = str(integrity.get("evidence_hash", ""))
    if integrity.get("algorithm") != "sha256" or not expected:
        return False
    payload = dict(package)
    payload.pop("integrity", None)
    payload.pop("generated_at", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest() == expected


if __name__ == "__main__":
    from benchmarks.isaac20_ablation import run_e3_benchmark
    from benchmarks.isaac20_fault_injection import run_e1_benchmark
    from benchmarks.isaac20_metrics import run_e2_metrics

    print(json.dumps(
        build_governance_evidence(
            e1_report=run_e1_benchmark(),
            e2_report=run_e2_metrics(),
            e3_report=run_e3_benchmark(),
        ),
        indent=2,
        sort_keys=True,
    ))
