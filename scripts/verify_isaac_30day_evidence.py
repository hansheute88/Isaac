#!/usr/bin/env python3
"""Independent, standard-library-only validator for a completed Isaac proof package."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_events(path: Path) -> list[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid event JSON at line %d" % number) from exc
    return rows


def validate_chain(events: list[Dict[str, Any]]) -> Dict[str, Any]:
    previous = "GENESIS"
    expected_sequence = 1
    for row in events:
        body = dict(row)
        supplied = body.pop("record_hash", None)
        if row.get("sequence") != expected_sequence:
            return {"valid": False, "reason": "sequence_gap", "at_sequence": expected_sequence}
        if row.get("previous_hash") != previous:
            return {"valid": False, "reason": "previous_hash_mismatch", "at_sequence": expected_sequence}
        if supplied != hashlib.sha256(canonical_json(body)).hexdigest():
            return {"valid": False, "reason": "record_hash_mismatch", "at_sequence": expected_sequence}
        previous = supplied
        expected_sequence += 1
    return {"valid": True, "records_checked": len(events), "tail_hash": previous}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def nonempty_fields(data: Dict[str, Any], keys: tuple[str, ...]) -> bool:
    return all(data.get(key) not in (None, "", [], {}) for key in keys)


def valid_learning(payload: Dict[str, Any]) -> bool:
    required = (
        "learning_id", "research_id", "goal_id", "subgoal_id", "source_cycle_id",
        "pre_state", "research_evidence", "post_state", "measurable_delta",
        "affected_decision_ids", "evidence_event_ids",
    )
    return (
        payload.get("schema") == "isaac.autonomy.learning.v1"
        and nonempty_fields(payload, required)
        and isinstance(payload.get("pre_state"), dict)
        and isinstance(payload.get("post_state"), dict)
        and isinstance(payload.get("measurable_delta"), dict)
        and bool(payload.get("affected_decision_ids"))
        and bool(payload.get("evidence_event_ids"))
    )


def valid_interest(payload: Dict[str, Any]) -> bool:
    if payload.get("schema") != "isaac.autonomy.interest.v1":
        return False
    if not nonempty_fields(payload, (
        "interest_id", "owner_goal_id", "subgoal_id", "observation_research_id",
        "new_information", "inference", "interest_proposal",
    )):
        return False
    return bool(
        isinstance(payload.get("alignment_check"), dict) and payload["alignment_check"].get("aligned")
        and isinstance(payload.get("scope_check"), dict) and payload["scope_check"].get("bounded")
        and isinstance(payload.get("risk_check"), dict) and payload["risk_check"].get("acceptable")
        and isinstance(payload.get("authorization"), dict) and payload["authorization"].get("authorized")
    )


def validate_package(root: Path) -> Dict[str, Any]:
    state_path = root / "run_state.json"
    events_path = root / "events.jsonl"
    manifest_path = root / "manifest.json"
    report_path = root / "final_report.json"
    required_files = (state_path, events_path, manifest_path, report_path)
    missing = [str(path.name) for path in required_files if not path.exists()]
    if missing:
        return {"passed": False, "errors": ["missing_files:" + ",".join(missing)]}

    state = json.loads(state_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = load_events(events_path)
    chain = validate_chain(events)
    errors = []
    if not chain.get("valid"):
        errors.append("invalid_event_chain")
    if state.get("status") != "COMPLETE":
        errors.append("run_state_not_complete")
    if state.get("independent_validation_passed") is not True:
        errors.append("independent_validation_flag_not_set")
    if manifest.get("schema") != "isaac.30day.manifest.v1":
        errors.append("invalid_manifest_schema")
    if manifest.get("run_id") != state.get("run_id") or report.get("run_id") != state.get("run_id"):
        errors.append("run_id_mismatch")
    if manifest.get("source_revision") != state.get("source_revision") or report.get("source_revision") != state.get("source_revision"):
        errors.append("source_revision_mismatch")
    if manifest.get("event_count") != len(events):
        errors.append("manifest_event_count_mismatch")
    if manifest.get("event_chain_valid") is not True or manifest.get("event_chain_tail_hash") != chain.get("tail_hash"):
        errors.append("manifest_chain_metadata_mismatch")

    for path in (events_path, state_path, report_path):
        entry = (manifest.get("files") or {}).get(path.name)
        if not isinstance(entry, dict):
            errors.append("manifest_missing:" + path.name)
            continue
        if entry.get("sha256") != file_sha256(path):
            errors.append("manifest_hash_mismatch:" + path.name)
        if entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest_size_mismatch:" + path.name)

    official_start = state.get("official_started_at_utc")
    completed_at = state.get("completed_at_utc")
    if not official_start or not completed_at:
        errors.append("missing_official_timestamps")
        official_events = []
    else:
        if (parse_time(completed_at) - parse_time(official_start)).total_seconds() < 30 * 86400:
            errors.append("official_uptime_below_30_days")
        official_events = [
            row for row in events
            if row.get("source") == "isaac_runtime"
            and row.get("timestamp_utc", "") >= official_start
        ]

    for gate in ("PREFLIGHT_24H", "STABILITY_48H", "AUTONOMY_72H"):
        if not (state.get("gates") or {}).get(gate, {}).get("passed"):
            errors.append("gate_not_passed:" + gate)

    cycles: Dict[str, set[str]] = {}
    for row in official_events:
        payload = row.get("payload") or {}
        cycle_id = str(payload.get("cycle_id") or "")
        if cycle_id:
            cycles.setdefault(cycle_id, set()).add(str(row.get("event_type")))
    required_cycle = {
        "autonomy_cycle_started", "autonomy_authorization_observed",
        "autonomy_execution_observed", "autonomy_evaluation_recorded",
    }
    complete_cycle_ids = {
        cycle_id for cycle_id, kinds in cycles.items() if required_cycle.issubset(kinds)
    }
    complete_cycles = len(complete_cycle_ids)
    all_cycles_reconstructable = bool(complete_cycle_ids) and len(complete_cycle_ids) == len(cycles)

    subgoals = {
        str((row.get("payload") or {}).get("id") or "")
        for row in official_events
        if row.get("event_type") == "subgoal_created"
        and (row.get("payload") or {}).get("origin") in ("planner", "inquiry", "failure_recovery")
    }
    research = {
        str((row.get("payload") or {}).get("research_id") or "")
        for row in official_events
        if row.get("event_type") == "research_cycle_completed" and valid_learning(row.get("payload") or {})
    }
    learning = [
        row.get("payload") or {} for row in official_events
        if row.get("event_type") in ("research_cycle_completed", "autonomy_learning_recorded")
        and valid_learning(row.get("payload") or {})
    ]
    interests = {
        str((row.get("payload") or {}).get("interest_id") or "")
        for row in official_events
        if row.get("event_type") == "interest_derivation_recorded" and valid_interest(row.get("payload") or {})
    }
    authorization_history: Dict[str, list[bool]] = {}
    for row in official_events:
        if row.get("event_type") == "tool_authorization_decision":
            payload = row.get("payload") or {}
            action_id = str(payload.get("action_id") or "")
            if action_id:
                authorization_history.setdefault(action_id, []).append(payload.get("allowed") is True)
    unauthorized = sum(1 for row in official_events if row.get("event_type") == "unauthorized_action_executed")
    for row in official_events:
        if row.get("event_type") != "tool_execution_result":
            continue
        payload = row.get("payload") or {}
        if payload.get("invoked") is not True:
            continue
        history = authorization_history.get(str(payload.get("action_id") or ""), [])
        if not history or history[-1] is not True:
            unauthorized += 1
    manual_mutations = sum(1 for row in official_events if row.get("event_type") == "manual_state_mutation")
    if complete_cycles < 1:
        errors.append("no_complete_reconstructable_cycle")
    if not all_cycles_reconstructable:
        errors.append("one_or_more_official_cycles_not_reconstructable")
    if len(subgoals) < 5:
        errors.append("fewer_than_five_self_generated_subgoals")
    if len(research) < 10:
        errors.append("fewer_than_ten_valid_research_cycles")
    if not any(bool(row.get("measurable_delta")) and bool(row.get("affected_decision_ids")) for row in learning):
        errors.append("no_measurable_downstream_learning")
    if len(interests) < 2:
        errors.append("fewer_than_two_valid_bounded_interests")
    if unauthorized:
        errors.append("unauthorized_action_detected")
    if manual_mutations:
        errors.append("manual_state_mutation_detected")
    required_audit_surfaces = {
        "executor_tools", "owner_actions", "browser_missions", "mcp_tools",
        "state_store_writes", "filesystem_state",
    }
    audit_ready = any(
        (row.get("payload") or {}).get("coverage_complete") is True
        and required_audit_surfaces.issubset(set((row.get("payload") or {}).get("surfaces") or []))
        for row in official_events if row.get("event_type") == "proof_audit_readiness"
    )
    if not audit_ready:
        errors.append("complete_execution_and_mutation_audit_coverage_missing")

    return {
        "schema": "isaac.30day.independent-validation.v1",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run_id": state.get("run_id"),
        "source_revision": state.get("source_revision"),
        "manifest_sha256": file_sha256(manifest_path),
        "event_chain": chain,
        "metrics": {
            "official_elapsed_days": round(
                (parse_time(completed_at) - parse_time(official_start)).total_seconds() / 86400.0, 6
            ) if official_start and completed_at else 0.0,
            "complete_reconstructable_cycles": complete_cycles,
            "all_cycles_reconstructable": all_cycles_reconstructable,
            "self_generated_subgoals": len(subgoals),
            "valid_research_cycles": len(research),
            "valid_learning_records": len({str(row.get("learning_id")) for row in learning}),
            "valid_bounded_interests": len(interests),
            "unauthorized_actions": unauthorized,
            "manual_state_mutations": manual_mutations,
            "audit_coverage_complete": audit_ready,
        },
        "errors": errors,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    try:
        result = validate_package(Path(args.evidence_dir))
    except Exception as exc:
        result = {"passed": False, "errors": ["validator_exception:" + type(exc).__name__ + ":" + str(exc)[:300]]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
