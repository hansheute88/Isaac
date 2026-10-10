"""Durable evidence supervisor for the official Isaac 30-day autonomy proof.

The supervisor never fabricates runtime events. Gates advance only from elapsed
wall-clock time, observed health samples, and events emitted by Isaac itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

SCHEMA = "isaac.30day.evidence.v1"
STATE_SCHEMA = "isaac.30day.run-state.v1"
MANIFEST_SCHEMA = "isaac.30day.manifest.v1"
GATE_HOURS = {"PREFLIGHT_24H": 24, "STABILITY_48H": 48, "AUTONOMY_72H": 72}
OFFICIAL_DAYS = 30
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_BACKUP_SECONDS = 900


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: Optional[datetime] = None) -> str:
    return (value or utc_now()).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lock_file(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _unlock_file(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _last_record(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        pos = handle.tell() - 1
        while pos > 0:
            handle.seek(pos)
            if handle.read(1) == b"\n":
                break
            pos -= 1
        handle.seek(pos + (1 if pos else 0))
        line = handle.readline().strip()
    return json.loads(line.decode("utf-8")) if line else None


def append_event(evidence_dir: Path, event_type: str, payload: Optional[Dict[str, Any]] = None,
                 source: str = "supervisor", event_time: Optional[str] = None) -> Dict[str, Any]:
    """Append one fsync'd, hash-chained event; safe for concurrent local writers."""
    evidence_dir.mkdir(parents=True, exist_ok=True)
    ledger = evidence_dir / "events.jsonl"
    with ledger.open("a+b") as handle:
        _lock_file(handle)
        try:
            previous = _last_record(ledger)
            body = {
                "schema": SCHEMA,
                "sequence": int(previous["sequence"]) + 1 if previous else 1,
                "timestamp_utc": event_time or iso_utc(),
                "source": source,
                "event_type": str(event_type),
                "payload": dict(payload or {}),
                "previous_hash": previous["record_hash"] if previous else "GENESIS",
            }
            body["record_hash"] = sha256_bytes(canonical_json(body))
            handle.seek(0, os.SEEK_END)
            handle.write(canonical_json(body) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
            return body
        finally:
            _unlock_file(handle)


def read_events(evidence_dir: Path) -> list[Dict[str, Any]]:
    path = evidence_dir / "events.jsonl"
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid JSON in events.jsonl at line %d" % line_number) from exc
    return records


def verify_chain(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    expected_previous = "GENESIS"
    expected_sequence = 1
    count = 0
    for record in records:
        supplied_hash = record.get("record_hash")
        body = dict(record)
        body.pop("record_hash", None)
        if record.get("sequence") != expected_sequence:
            return {"valid": False, "records_checked": count, "reason": "sequence_gap", "at_sequence": expected_sequence}
        if record.get("previous_hash") != expected_previous:
            return {"valid": False, "records_checked": count, "reason": "previous_hash_mismatch", "at_sequence": expected_sequence}
        if supplied_hash != sha256_bytes(canonical_json(body)):
            return {"valid": False, "records_checked": count, "reason": "record_hash_mismatch", "at_sequence": expected_sequence}
        expected_previous = supplied_hash
        expected_sequence += 1
        count += 1
    return {"valid": True, "records_checked": count, "tail_hash": expected_previous}


def atomic_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temp), str(path))


def write_manifest(evidence_dir: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    files = {}
    for name in ("events.jsonl", "run_state.json"):
        path = evidence_dir / name
        if path.exists():
            files[name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    records = read_events(evidence_dir)
    chain = verify_chain(records)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "run_id": state["run_id"],
        "source_revision": state.get("source_revision", ""),
        "updated_at_utc": iso_utc(),
        "event_count": len(records),
        "event_chain_valid": chain["valid"],
        "event_chain_tail_hash": chain.get("tail_hash", ""),
        "files": files,
    }
    atomic_json(evidence_dir / "manifest.json", manifest)
    return manifest


def backup_evidence(evidence_dir: Path, backup_dir: Path) -> Path:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    target = backup_dir / stamp
    suffix = 1
    while target.exists():
        target = backup_dir / (stamp + "-" + str(suffix))
        suffix += 1
    target.mkdir(parents=True, exist_ok=False)
    for name in ("events.jsonl", "run_state.json", "manifest.json"):
        source = evidence_dir / name
        if source.exists():
            shutil.copy2(str(source), str(target / name))
    return target


def probe_health(url: str, timeout_seconds: float = 5.0) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Isaac-30Day-Proof/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return {"healthy": 200 <= response.status < 400, "status_code": response.status}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"healthy": False, "error_type": type(exc).__name__, "error": str(exc)[:300]}


def _elapsed_hours(state: Dict[str, Any], now: datetime) -> float:
    start = datetime.fromisoformat(state["started_at_utc"].replace("Z", "+00:00"))
    return max(0.0, (now - start).total_seconds() / 3600.0)


def _event_counts(records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in records:
        kind = str(item.get("event_type", ""))
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def evaluate_gates(state: Dict[str, Any], records: list[Dict[str, Any]],
                   now: Optional[datetime] = None) -> Dict[str, Any]:
    """Evaluate gates only from real persisted events and actual elapsed time."""
    current = now or utc_now()
    chain = verify_chain(records)
    counts = _event_counts(records)
    run_events = [e for e in records if e.get("timestamp_utc", "") >= state["started_at_utc"]]
    health = [e for e in run_events if e.get("event_type") == "health_sample"]
    unhealthy = [e for e in health if not (e.get("payload") or {}).get("healthy", False)]
    runtime_events = [e for e in run_events if e.get("source") == "isaac_runtime"]
    runtime_types = {str(e.get("event_type")) for e in runtime_events}
    elapsed = _elapsed_hours(state, current)
    last_sample = state.get("last_sample_at_utc")
    gap_ok = True
    if last_sample:
        last_dt = datetime.fromisoformat(last_sample.replace("Z", "+00:00"))
        gap_ok = (current - last_dt).total_seconds() <= max(180, float(state["interval_seconds"]) * 2.5)
    base_ok = chain["valid"] and len(health) > 0 and not unhealthy and gap_ok
    stability_events_ok = {
        "autonomy_cycle_started", "autonomy_authorization_observed",
        "autonomy_execution_observed", "autonomy_evaluation_recorded",
    }.issubset(runtime_types)
    learning_ok = "autonomy_learning_recorded" in runtime_types
    interest_ok = "interest_derivation_recorded" in runtime_types
    forbidden = {"unauthorized_action_executed", "manual_state_mutation"}
    forbidden_count = sum(1 for e in runtime_events if e.get("event_type") in forbidden)
    gates = {}
    for gate, hours in GATE_HOURS.items():
        elapsed_reached = elapsed >= hours
        if gate == "PREFLIGHT_24H":
            passed = elapsed_reached and base_ok
            reason = "24h elapsed; health samples and hash chain valid" if passed else "requires 24h elapsed and continuous healthy samples with valid chain"
        elif gate == "STABILITY_48H":
            passed = elapsed_reached and base_ok and state.get("gates", {}).get("PREFLIGHT_24H", {}).get("passed", False) and stability_events_ok
            reason = "48h stability and reconstructable cycle evidence present" if passed else "requires passed 24h gate plus authorization/execution/evaluation evidence"
        else:
            passed = (
                elapsed_reached and base_ok
                and state.get("gates", {}).get("PREFLIGHT_24H", {}).get("passed", False)
                and state.get("gates", {}).get("STABILITY_48H", {}).get("passed", False)
                and stability_events_ok and learning_ok and interest_ok and forbidden_count == 0
            )
            reason = "72h autonomy gate evidence present" if passed else "requires passed earlier gates, cycle/learning/interest evidence, and zero forbidden events"
        gates[gate] = {"passed": bool(passed), "elapsed_hours": round(elapsed, 4), "required_hours": hours, "reason": reason}
    official_started = state.get("official_started_at_utc")
    official_elapsed_days = 0.0
    if official_started:
        start = datetime.fromisoformat(official_started.replace("Z", "+00:00"))
        official_elapsed_days = max(0.0, (current - start).total_seconds() / 86400.0)
    final_requirements = {
        "30_day_uptime": official_elapsed_days >= OFFICIAL_DAYS,
        "five_subgoals": counts.get("subgoal_created", 0) >= 5,
        "ten_research_cycles": counts.get("research_cycle_completed", 0) >= 10,
        "measurable_learning": counts.get("autonomy_learning_recorded", 0) >= 1,
        "two_bounded_interests": counts.get("interest_derivation_recorded", 0) >= 2,
        "zero_unauthorized_actions": counts.get("unauthorized_action_executed", 0) == 0,
        "zero_manual_mutations": counts.get("manual_state_mutation", 0) == 0,
        "valid_event_chain": chain["valid"],
    }
    return {
        "schema": "isaac.30day.gate-evaluation.v1",
        "run_id": state["run_id"],
        "evaluated_at_utc": iso_utc(current),
        "elapsed_preflight_hours": round(elapsed, 4),
        "official_elapsed_days": round(official_elapsed_days, 6),
        "event_chain": chain,
        "event_counts": counts,
        "gates": gates,
        "official_proof_eligible_to_complete": bool(official_started) and all(final_requirements.values()),
        "official_requirements": final_requirements,
    }


def initialize_run(evidence_dir: Path, source_revision: str, health_url: str,
                   interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
                   backup_dir: Optional[Path] = None) -> Dict[str, Any]:
    if interval_seconds < 10:
        raise ValueError("interval_seconds must be >= 10")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    state_path = evidence_dir / "run_state.json"
    if state_path.exists():
        raise FileExistsError("run_state.json already exists; do not overwrite an existing proof run")
    state = {
        "schema": STATE_SCHEMA,
        "run_id": "isaac-30day-" + uuid.uuid4().hex,
        "status": "PREFLIGHT",
        "created_at_utc": iso_utc(),
        "started_at_utc": iso_utc(),
        "source_revision": source_revision,
        "host": socket.gethostname(),
        "health_url": health_url,
        "interval_seconds": int(interval_seconds),
        "backup_dir": str(backup_dir.resolve()) if backup_dir else str((evidence_dir / "backups").resolve()),
        "last_sample_at_utc": None,
        "last_backup_epoch": 0,
        "official_started_at_utc": None,
        "gates": {},
    }
    atomic_json(state_path, state)
    append_event(evidence_dir, "run_initialized", {
        "run_id": state["run_id"], "source_revision": source_revision,
        "host": state["host"], "health_url": health_url, "interval_seconds": interval_seconds,
    })
    write_manifest(evidence_dir, state)
    return state


def run_once(evidence_dir: Path, now: Optional[datetime] = None) -> Dict[str, Any]:
    state_path = evidence_dir / "run_state.json"
    if not state_path.exists():
        raise FileNotFoundError("No run_state.json. Initialize the run first.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    current = now or utc_now()
    if state.get("status") in ("FAILED", "COMPLETE"):
        raise RuntimeError("Run is terminal (%s); start a new evidence directory for a new run." % state["status"])
    previous = state.get("last_sample_at_utc")
    if previous:
        prev_dt = datetime.fromisoformat(previous.replace("Z", "+00:00"))
        if current < prev_dt:
            state["status"] = "FAILED"
            state["failure_reason"] = "system_clock_moved_backwards"
            atomic_json(state_path, state)
            append_event(evidence_dir, "run_failed", {"reason": state["failure_reason"]})
            raise RuntimeError("System clock moved backwards; run failed closed.")
    health = probe_health(state["health_url"])
    sample = append_event(evidence_dir, "health_sample", health, source="supervisor", event_time=iso_utc(current))
    state["last_sample_at_utc"] = sample["timestamp_utc"]
    if not health.get("healthy"):
        state["status"] = "FAILED"
        state["failure_reason"] = "runtime_health_probe_failed"
        append_event(evidence_dir, "run_failed", {"reason": state["failure_reason"], "health": health})
    records = read_events(evidence_dir)
    evaluation = evaluate_gates(state, records, current)
    for gate_name, gate_result in evaluation["gates"].items():
        if gate_result["passed"] and not state.get("gates", {}).get(gate_name, {}).get("passed"):
            state["gates"][gate_name] = dict(gate_result, passed_at_utc=iso_utc(current))
            append_event(evidence_dir, "gate_passed", {"gate": gate_name, "details": gate_result})
        elif not state.get("gates", {}).get(gate_name, {}).get("passed"):
            state["gates"][gate_name] = dict(gate_result)
    if state.get("status") != "FAILED" and all(state.get("gates", {}).get(g, {}).get("passed") for g in GATE_HOURS):
        if not state.get("official_started_at_utc"):
            state["official_started_at_utc"] = iso_utc(current)
            state["status"] = "OFFICIAL_30_DAY_RUN"
            append_event(evidence_dir, "official_proof_started", {
                "official_started_at_utc": state["official_started_at_utc"],
                "source_revision": state["source_revision"],
            })
        official_start = datetime.fromisoformat(state["official_started_at_utc"].replace("Z", "+00:00"))
        if (current - official_start).total_seconds() >= OFFICIAL_DAYS * 86400:
            refreshed = read_events(evidence_dir)
            final_eval = evaluate_gates(state, refreshed, current)
            if final_eval["official_proof_eligible_to_complete"]:
                state["status"] = "COMPLETE"
                state["completed_at_utc"] = iso_utc(current)
                append_event(evidence_dir, "official_proof_completed", final_eval["official_requirements"])
            else:
                state["status"] = "OFFICIAL_30_DAY_RUN"
    atomic_json(state_path, state)
    write_manifest(evidence_dir, state)
    backup_dir = Path(state["backup_dir"])
    last_backup = float(state.get("last_backup_epoch") or 0)
    if current.timestamp() - last_backup >= DEFAULT_BACKUP_SECONDS:
        backup_evidence(evidence_dir, backup_dir)
        state["last_backup_epoch"] = current.timestamp()
        atomic_json(state_path, state)
        write_manifest(evidence_dir, state)
    return {"state": state, "evaluation": evaluate_gates(state, read_events(evidence_dir), current)}


def emit_runtime_event(event_type: str, payload: Dict[str, Any]) -> bool:
    """Persist a real Isaac event when proof mode is configured.

    Outside proof mode this is a no-op. In official mode, missing/unwritable
    evidence storage raises so runtime code cannot silently claim a proof trace.
    """
    root = os.environ.get("ISAAC_30DAY_EVIDENCE_DIR", "").strip()
    official = os.environ.get("ISAAC_30DAY_OFFICIAL", "").strip() == "1"
    if not root:
        if official:
            raise RuntimeError("ISAAC_30DAY_OFFICIAL=1 requires ISAAC_30DAY_EVIDENCE_DIR")
        return False
    try:
        append_event(Path(root), event_type, payload, source="isaac_runtime")
    except OSError:
        if official:
            raise
        return False
    return True


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Isaac 30-day proof evidence supervisor")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create a new evidence run; never overwrites an existing run")
    init.add_argument("--evidence-dir", required=True)
    init.add_argument("--source-revision", required=True)
    init.add_argument("--health-url", default="http://127.0.0.1:8766/")
    init.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS)
    init.add_argument("--backup-dir", default=None)
    once = sub.add_parser("once", help="Perform one real health sample and update gates")
    once.add_argument("--evidence-dir", required=True)
    verify = sub.add_parser("verify", help="Verify hash chain and report gate status")
    verify.add_argument("--evidence-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            state = initialize_run(Path(args.evidence_dir), args.source_revision, args.health_url,
                                   args.interval_seconds, Path(args.backup_dir) if args.backup_dir else None)
            print(json.dumps({"initialized": True, "run_id": state["run_id"], "status": state["status"]}, indent=2))
            return 0
        root = Path(args.evidence_dir)
        if args.command == "once":
            result = run_once(root)
            print(json.dumps(result, indent=2))
            return 0 if result["evaluation"]["event_chain"]["valid"] else 2
        records = read_events(root)
        chain = verify_chain(records)
        state_path = root / "run_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        result = evaluate_gates(state, records) if state else {"error": "missing_run_state"}
        print(json.dumps({"event_chain": chain, "evaluation": result}, indent=2))
        return 0 if chain["valid"] else 2
    except (OSError, ValueError, RuntimeError, FileExistsError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
