"""Isaac 2.0 F2 — reproducibility and provenance manifest.

F2 binds an F1 governance evidence package to the source revision and benchmark
contracts that produced it. The manifest is deliberately an engineering
provenance artifact, not a legal-compliance determination.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "isaac20-governance-repro-v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_reproducibility_manifest(
    *,
    evidence_package: Mapping[str, Any],
    source_revision: str,
    workflow_run_id: str | None = None,
    workflow_name: str | None = None,
) -> dict[str, Any]:
    """Create provenance that can be independently checked against F1."""
    integrity = evidence_package.get("integrity", {})
    benchmark_contracts = {
        name: {
            "schema_version": report.get("schema_version"),
            "passed": report.get("passed"),
        }
        for name, report in evidence_package.get("benchmarks", {}).items()
    }
    body = {
        "schema_version": SCHEMA_VERSION,
        "source_revision": source_revision,
        "workflow": {
            "run_id": workflow_run_id or "",
            "name": workflow_name or "",
        },
        "evidence": {
            "schema_version": evidence_package.get("schema_version"),
            "evidence_hash": integrity.get("evidence_hash"),
            "hash_algorithm": integrity.get("algorithm"),
        },
        "benchmark_contracts": benchmark_contracts,
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def verify_reproducibility_manifest(
    manifest: Mapping[str, Any],
    *,
    evidence_package: Mapping[str, Any],
) -> bool:
    """Verify both manifest integrity and its binding to the supplied F1 package."""
    expected = str(manifest.get("manifest_hash", ""))
    if manifest.get("schema_version") != SCHEMA_VERSION or not expected:
        return False

    payload = dict(manifest)
    payload.pop("manifest_hash", None)
    if sha256_json(payload) != expected:
        return False

    integrity = evidence_package.get("integrity", {})
    evidence = manifest.get("evidence", {})
    if evidence.get("schema_version") != evidence_package.get("schema_version"):
        return False
    if evidence.get("evidence_hash") != integrity.get("evidence_hash"):
        return False
    if evidence.get("hash_algorithm") != integrity.get("algorithm"):
        return False

    contracts = manifest.get("benchmark_contracts", {})
    benchmarks = evidence_package.get("benchmarks", {})
    if set(contracts) != set(benchmarks):
        return False
    for name, contract in contracts.items():
        report = benchmarks[name]
        if contract.get("schema_version") != report.get("schema_version"):
            return False
        if contract.get("passed") != report.get("passed"):
            return False
    return True
