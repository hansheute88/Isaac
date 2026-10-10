"""Windows-friendly controller for the gated Isaac 30-day autonomy proof.

This controller records observations; it never fabricates runtime evidence or
marks a gate passed solely because time elapsed. All gate approvals require a
machine-readable evidence report and verified journal continuity.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "isaac.30day.run.v1"
PHASES = [
    ("PREFLIGHT", 24 * 3600),
    ("STABILITY", 48 * 3600),
    ("AUTONOMY", 72 * 3600),
    ("OFFICIAL", 30 * 24 * 3600),
]
EVENTS = "events.jsonl"
STATE = "run-state.json"
TRACE = "runtime-trace.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_dir_default() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Isaac" / "autonomy-30day"


def load_state(root: Path) -> dict[str, Any]:
    path = root / STATE
    if not path.exists():
        raise RuntimeError(f"Run not initialized: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_journal(root: Path) -> dict[str, Any]:
    path = root / EVENTS
    if not path.exists():
        return {"valid": False, "reason": "journal_missing", "events": 0}
    previous = "0" * 64
    count = 0
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                item = json.loads(line)
                claimed = item.pop("hash")
                if item.get("previous_hash") != previous:
                    return {"valid": False, "reason": "previous_hash_mismatch", "line": line_no, "events": count}
                actual = hashlib.sha256(canonical(item)).hexdigest()
                if actual != claimed:
                    return {"valid": False, "reason": "event_hash_mismatch", "line": line_no, "events": count}
                previous = claimed
                count += 1
    except (OSError, ValueError, KeyError) as exc:
        return {"valid": False, "reason": f"journal_parse_error:{type(exc).__name__}", "events": count}
    state = load_state(root)
    if count != state.get("journal_events") or previous != state.get("journal_head_hash"):
        return {"valid": False, "reason": "state_journal_head_mismatch", "events": count}
    return {"valid": True, "events": count, "head_hash": previous}


def append_event(root: Path, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    state = load_state(root)
    check = verify_journal(root)
    if not check["valid"]:
        raise RuntimeError(f"Evidence journal failed closed: {check}")
    event = {
        "schema": SCHEMA,
        "sequence": check["events"] + 1,
        "timestamp_utc": utc_now(),
        "event_type": event_type,
        "payload": payload or {},
        "previous_hash": check["head_hash"],
    }
    event_hash = hashlib.sha256(canonical(event)).hexdigest()
    event["hash"] = event_hash
    with (root / EVENTS).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(event).decode("utf-8") + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    state["journal_events"] = event["sequence"]
    state["journal_head_hash"] = event_hash
    state["updated_at_utc"] = utc_now()
    atomic_json(root / STATE, state)
    return event


def backup(root: Path, destination: Path) -> dict[str, Any]:
    root_resolved = root.resolve()
    dest_resolved = destination.resolve()
    if dest_resolved == root_resolved or root_resolved in dest_resolved.parents:
        raise ValueError("Backup directory must be outside the run directory.")
    dest_resolved.mkdir(parents=True, exist_ok=True)
    target = dest_resolved / root.name
    if target.resolve() == root_resolved or target.resolve() in root_resolved.parents or root_resolved in target.resolve().parents:
        raise ValueError("Backup target must not overlap the run directory.")
    target.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in (STATE, EVENTS, TRACE):
        source = root / name
        if source.exists():
            shutil.copy2(source, target / name)
            files[name] = sha256_file(target / name)
    report = {"schema": "isaac.30day.backup.v1", "created_at_utc": utc_now(), "source": str(root), "files": files}
    atomic_json(target / "backup-manifest.json", report)
    return report


def init_run(root: Path, source_revision: str, backup_dir: Path) -> None:
    if root.exists() and any(root.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty run directory: {root}")
    if len(source_revision) != 40 or any(c not in "0123456789abcdefABCDEF" for c in source_revision):
        raise ValueError("--source-revision must be the exact 40-character Git commit SHA.")
    root.mkdir(parents=True, exist_ok=True)
    state = {
        "schema": SCHEMA,
        "run_id": f"isaac-30day-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "source_revision": source_revision.lower(),
        "phase": "PREFLIGHT",
        "phase_started_at_utc": utc_now(),
        "official_started_at_utc": None,
        "official_ends_at_utc": None,
        "continuous_since_utc": None,
        "last_heartbeat_at_utc": None,
        "last_backup_at_utc": None,
        "backup_dir": str(backup_dir.resolve()),
        "journal_events": 0,
        "journal_head_hash": "0" * 64,
        "runtime_pid": None,
        "manual_state_mutations": 0,
        "unauthorized_actions": 0,
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
    }
    atomic_json(root / STATE, state)
    (root / EVENTS).write_text("", encoding="utf-8")
    append_event(root, "run_initialized", {"source_revision": source_revision.lower(), "phase": "PREFLIGHT"})
    print(json.dumps({"run_dir": str(root), "run_id": state["run_id"], "phase": "PREFLIGHT", "official_clock_started": False}, indent=2))


def port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def runtime_trace_stats(root: Path) -> dict[str, Any]:
    path = root / TRACE
    if not path.exists():
        return {"exists": False, "entries": 0, "sha256": None, "bytes": 0}
    count = 0
    malformed = 0
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                json.loads(line)
                count += 1
            except ValueError:
                malformed += 1
    return {"exists": True, "entries": count, "malformed_lines": malformed, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def monitor(root: Path, pid: int, interval: int, backup_interval: int, once: bool = False) -> None:
    state = load_state(root)
    state["runtime_pid"] = pid
    state["continuous_since_utc"] = state.get("continuous_since_utc") or utc_now()
    atomic_json(root / STATE, state)
    append_event(root, "monitor_started", {"pid": pid, "interval_seconds": interval})
    last_backup = time.monotonic()
    while True:
        alive = pid_alive(pid)
        http_ok = port_open("127.0.0.1", 8766)
        ws_ok = port_open("127.0.0.1", 8765)
        trace = runtime_trace_stats(root)
        payload = {"pid": pid, "pid_alive": alive, "dashboard_port_8766_open": http_ok,
                   "websocket_port_8765_open": ws_ok, "runtime_trace": trace}
        append_event(root, "heartbeat", payload)
        state = load_state(root)
        state["last_heartbeat_at_utc"] = utc_now()
        if not alive:
            state["continuous_since_utc"] = None
        atomic_json(root / STATE, state)
        if time.monotonic() - last_backup >= backup_interval:
            report = backup(root, Path(state["backup_dir"]))
            state = load_state(root)
            state["last_backup_at_utc"] = utc_now()
            atomic_json(root / STATE, state)
            append_event(root, "backup_completed", {"manifest_sha256": sha256_file(Path(state["backup_dir"]) / root.name / "backup-manifest.json"), "files": report["files"]})
            last_backup = time.monotonic()
        print(json.dumps({"timestamp_utc": utc_now(), **payload}, ensure_ascii=False), flush=True)
        if once or not alive:
            if not alive:
                append_event(root, "runtime_process_not_alive", {"pid": pid})
            break
        time.sleep(max(5, interval))


def approve_gate(root: Path, gate: str, evidence_path: Path) -> None:
    state = load_state(root)
    check = verify_journal(root)
    if not check["valid"]:
        raise RuntimeError(f"Journal invalid: {check}")
    expected = {"PREFLIGHT": "PREFLIGHT", "STABILITY": "STABILITY", "AUTONOMY": "AUTONOMY"}
    if gate not in expected or state["phase"] != gate:
        raise RuntimeError(f"Gate {gate} cannot be approved while phase is {state['phase']}.")
    durations = dict(PHASES)
    phase_started = datetime.fromisoformat(state["phase_started_at_utc"])
    elapsed = (datetime.now(timezone.utc) - phase_started).total_seconds()
    if elapsed < durations[gate]:
        raise RuntimeError(f"Gate duration incomplete: {elapsed:.0f}s elapsed; {durations[gate]}s required.")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    required = {
        "PREFLIGHT": ["runtime_trace_enabled", "backup_verified", "journal_chain_valid", "authorization_tests_passed"],
        "STABILITY": ["runtime_health_stable", "no_unexplained_restarts", "backup_verified", "journal_chain_valid"],
        "AUTONOMY": ["cycles_reconstructable", "learning_effect_measured", "interest_derivations_valid", "zero_unauthorized_actions", "zero_manual_state_mutations", "backup_verified", "journal_chain_valid"],
    }[gate]
    failed = [key for key in required if evidence.get(key) is not True]
    if failed:
        raise RuntimeError(f"Gate evidence incomplete or failed: {failed}")
    append_event(root, "gate_approved", {"gate": gate, "evidence_file": str(evidence_path.resolve()), "evidence_sha256": sha256_file(evidence_path), "checks": required})
    next_phase = {"PREFLIGHT": "STABILITY", "STABILITY": "AUTONOMY", "AUTONOMY": "OFFICIAL"}[gate]
    state = load_state(root)
    state["phase"] = next_phase
    state["phase_started_at_utc"] = utc_now()
    if next_phase == "OFFICIAL":
        state["official_started_at_utc"] = utc_now()
        state["official_ends_at_utc"] = (datetime.now(timezone.utc).timestamp() + 30 * 86400)
    atomic_json(root / STATE, state)
    append_event(root, "phase_started", {"phase": next_phase, "official_clock_started": next_phase == "OFFICIAL"})
    print(json.dumps({"approved_gate": gate, "next_phase": next_phase, "official_clock_started": next_phase == "OFFICIAL"}, indent=2))


def status(root: Path) -> None:
    state = load_state(root)
    integrity = verify_journal(root)
    phase = state["phase"]
    duration = dict(PHASES).get(phase)
    elapsed = None
    if duration is not None:
        elapsed = max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(state["phase_started_at_utc"])).total_seconds())
    official_remaining = None
    if state.get("official_ends_at_utc"):
        official_remaining = max(0, state["official_ends_at_utc"] - datetime.now(timezone.utc).timestamp())
    print(json.dumps({"state": state, "journal_integrity": integrity, "phase_elapsed_seconds": elapsed,
                      "phase_required_seconds": duration, "official_remaining_seconds": official_remaining,
                      "runtime_trace": runtime_trace_stats(root)}, indent=2, ensure_ascii=False))


def verify_and_manifest(root: Path) -> None:
    state = load_state(root)
    integrity = verify_journal(root)
    if not integrity["valid"]:
        raise RuntimeError(f"Evidence integrity check failed: {integrity}")
    trace = runtime_trace_stats(root)
    manifest = {
        "schema": "isaac.30day.final-manifest.v1",
        "run_id": state["run_id"],
        "source_revision": state["source_revision"],
        "phase": state["phase"],
        "official_started_at_utc": state.get("official_started_at_utc"),
        "official_ends_at_utc": state.get("official_ends_at_utc"),
        "generated_at_utc": utc_now(),
        "journal_integrity": integrity,
        "files": {},
        "runtime_trace": trace,
        "note": "A valid hash chain proves internal consistency only; independent backup and runtime evidence review are still required.",
    }
    for name in (STATE, EVENTS, TRACE):
        path = root / name
        if path.exists():
            manifest["files"][name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    atomic_json(root / "sha256-manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=run_dir_default())
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--source-revision", required=True)
    init.add_argument("--backup-dir", type=Path, required=True)
    mon = sub.add_parser("monitor")
    mon.add_argument("--pid", type=int, required=True)
    mon.add_argument("--interval", type=int, default=60)
    mon.add_argument("--backup-interval", type=int, default=900)
    mon.add_argument("--once", action="store_true")
    gate = sub.add_parser("approve-gate")
    gate.add_argument("--gate", choices=["PREFLIGHT", "STABILITY", "AUTONOMY"], required=True)
    gate.add_argument("--evidence", type=Path, required=True)
    sub.add_parser("status")
    sub.add_parser("backup-now")
    sub.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_run(args.run_dir, args.source_revision, args.backup_dir)
        elif args.command == "monitor":
            monitor(args.run_dir, args.pid, args.interval, args.backup_interval, args.once)
        elif args.command == "approve-gate":
            approve_gate(args.run_dir, args.gate, args.evidence)
        elif args.command == "status":
            status(args.run_dir)
        elif args.command == "backup-now":
            state = load_state(args.run_dir)
            report = backup(args.run_dir, Path(state["backup_dir"]))
            append_event(args.run_dir, "backup_completed", {"files": report["files"]})
            state = load_state(args.run_dir)
            state["last_backup_at_utc"] = utc_now()
            atomic_json(args.run_dir / STATE, state)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.command == "verify":
            verify_and_manifest(args.run_dir)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
