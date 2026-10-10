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
    for name in (STATE, EVENTS, TRACE, "preflight-tests.json", "preflight-tests.stdout.log", "preflight-tests.stderr.log", "isaac-stdout.log", "isaac-stderr.log"):
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
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if index == len(lines) - 1 and not line.endswith("\n"):
            continue
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)
    for index, line in enumerate(lines):
        # The runtime appends events while the monitor reads. Ignore only an
        # incomplete final line; malformed completed lines remain fatal.
        if index == len(lines) - 1 and not line.endswith("\n"):
            continue
        if line.strip():
            rows.append(json.loads(line))
    return rows


def verify_backup(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    target = Path(state["backup_dir"]) / root.name
    manifest_path = target / "backup-manifest.json"
    if not manifest_path.exists():
        return {"valid": False, "reason": "backup_manifest_missing"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, expected in manifest.get("files", {}).items():
            candidate = target / name
            if not candidate.exists() or sha256_file(candidate) != expected:
                return {"valid": False, "reason": f"backup_hash_mismatch:{name}"}
        copied_journal = verify_journal(target)
        if not copied_journal["valid"]:
            return {"valid": False, "reason": "backup_journal_invalid", "detail": copied_journal}
        last_backup = state.get("last_backup_at_utc")
        age = None if not last_backup else (datetime.now(timezone.utc) - datetime.fromisoformat(last_backup)).total_seconds()
        if age is None or age > 1800:
            return {"valid": False, "reason": "backup_stale", "age_seconds": age}
        return {"valid": True, "age_seconds": age, "manifest_sha256": sha256_file(manifest_path)}
    except (OSError, ValueError, KeyError) as exc:
        return {"valid": False, "reason": f"backup_validation_error:{type(exc).__name__}"}


def trace_gate_metrics(root: Path) -> dict[str, Any]:
    try:
        rows = read_jsonl(root / TRACE)
    except (OSError, ValueError):
        return {"valid_jsonl": False, "cycles_reconstructable": 0, "subgoals": 0, "research_cycles": 0,
                "learning_effects": 0, "valid_interests": 0, "audit_snapshots": []}
    cycles: dict[str, set[str]] = {}
    subgoals = research = learning = interests = 0
    audit_snapshots = []
    for row in rows:
        data = row.get("data") or {}
        event = str(row.get("event") or "")
        cid = str(data.get("cycle_id") or "")
        if cid:
            cycles.setdefault(cid, set()).add(event)
        if event in {"subgoal_created", "autonomy_subgoal_created"}:
            subgoals += 1
        if event in {"research_cycle_completed", "autonomy_research_completed"}:
            research += 1
        if event in {"learning_record_created", "autonomy_learning_record_created"}:
            if (isinstance(data.get("pre_state"), dict) and isinstance(data.get("post_state"), dict)
                    and isinstance(data.get("measurable_delta"), dict) and data.get("measurable_delta")
                    and isinstance(data.get("affected_decision_ids"), list) and data.get("affected_decision_ids")):
                learning += 1
        if event == "interest_derivation_recorded" and (data.get("validation") or {}).get("valid") is True:
            interests += 1
        if event in {"governance_audit_snapshot", "autonomy_audit_snapshot"}:
            audit_snapshots.append({"ts": float(row.get("ts") or 0), **data})
    complete = sum(
        1 for events in cycles.values()
        if "autonomy_cycle_started" in events
        and "autonomy_authorization_observed" in events
        and "autonomy_execution_observed" in events
        and "autonomy_evaluation_recorded" in events
    )
    return {"valid_jsonl": True, "cycles_reconstructable": complete, "subgoals": subgoals,
            "research_cycles": research, "learning_effects": learning, "valid_interests": interests,
            "audit_snapshots": audit_snapshots}


def approve_gate(root: Path, gate: str) -> None:
    state = load_state(root)
    check = verify_journal(root)
    if not check["valid"]:
        raise RuntimeError(f"Journal invalid: {check}")
    if gate not in {"PREFLIGHT", "STABILITY", "AUTONOMY"} or state["phase"] != gate:
        raise RuntimeError(f"Gate {gate} cannot be approved while phase is {state['phase']}.")
    durations = dict(PHASES)
    phase_started = datetime.fromisoformat(state["phase_started_at_utc"])
    elapsed = (datetime.now(timezone.utc) - phase_started).total_seconds()
    trace = runtime_trace_stats(root)
    metrics = trace_gate_metrics(root)
    backup_check = verify_backup(root, state)
    events = read_jsonl(root / EVENTS)
    test_report_path = root / "preflight-tests.json"
    test_report = {}
    test_report_valid = False
    if test_report_path.exists():
        try:
            test_report = json.loads(test_report_path.read_text(encoding="utf-8"))
            stdout_log = root / "preflight-tests.stdout.log"
            stderr_log = root / "preflight-tests.stderr.log"
            test_report_valid = (
                test_report.get("schema") == "isaac.30day.preflight-tests.v1"
                and test_report.get("exit_code") == 0
                and test_report.get("source_revision") == state["source_revision"]
                and stdout_log.exists() and stderr_log.exists()
                and sha256_file(stdout_log) == test_report.get("stdout_sha256")
                and sha256_file(stderr_log) == test_report.get("stderr_sha256")
            )
        except (OSError, ValueError):
            test_report_valid = False
    heartbeats = [e for e in events if e.get("event_type") == "heartbeat"
                  and datetime.fromisoformat(e["timestamp_utc"]) >= phase_started]
    phase_heartbeat_ok = bool(heartbeats)
    if phase_heartbeat_ok:
        stamps = [datetime.fromisoformat(e["timestamp_utc"]).timestamp() for e in heartbeats]
        phase_heartbeat_ok = stamps[-1] >= time.time() - 180 and stamps[0] <= phase_started.timestamp() + 180
        phase_heartbeat_ok = phase_heartbeat_ok and all((b - a) <= 180 for a, b in zip(stamps, stamps[1:]))
        phase_heartbeat_ok = phase_heartbeat_ok and all(
            (e.get("payload") or {}).get("pid_alive") is True
            and (e.get("payload") or {}).get("dashboard_port_8766_open") is True
            and (e.get("payload") or {}).get("websocket_port_8765_open") is True
            for e in heartbeats
        )
    recent_audits = [a for a in metrics["audit_snapshots"] if a["ts"] >= phase_started.timestamp()]
    audit = recent_audits[-1] if recent_audits else {}
    if elapsed < durations[gate]:
        checks = {"required_phase_duration_elapsed": False}
    elif gate == "PREFLIGHT":
        checks = {
            "runtime_trace_enabled": trace["exists"] and trace["entries"] > 0 and metrics["valid_jsonl"],
            "backup_verified": backup_check["valid"],
            "journal_chain_valid": check["valid"],
            "authorization_tests_passed": test_report_valid,
        }
    elif gate == "STABILITY":
        checks = {
            "runtime_health_stable": phase_heartbeat_ok,
            "no_unexplained_restarts": not any(
                e.get("event_type") == "runtime_process_not_alive"
                and datetime.fromisoformat(e["timestamp_utc"]) >= phase_started for e in events
            ),
            "backup_verified": backup_check["valid"],
            "journal_chain_valid": check["valid"],
        }
    else:
        checks = {
            "cycles_reconstructable": metrics["cycles_reconstructable"] >= 1,
            "subgoals_minimum": metrics["subgoals"] >= 5,
            "research_cycles_minimum": metrics["research_cycles"] >= 10,
            "learning_effect_measured": metrics["learning_effects"] >= 1,
            "interest_derivations_valid": metrics["valid_interests"] >= 2,
            "zero_unauthorized_actions": audit.get("coverage_complete") is True
                and audit.get("unauthorized_actions_count") == 0,
            "zero_manual_state_mutations": audit.get("coverage_complete") is True
                and audit.get("manual_state_mutations") == 0,
            "audit_snapshot_current": bool(audit) and audit["ts"] >= time.time() - 600,
            "backup_verified": backup_check["valid"],
            "journal_chain_valid": check["valid"],
        }
    report = {
        "schema": "isaac.30day.gate-evidence.v1",
        "run_id": state["run_id"],
        "gate": gate,
        "generated_at_utc": utc_now(),
        "source_revision": state["source_revision"],
        "phase_elapsed_seconds": elapsed,
        "phase_required_seconds": durations[gate],
        "journal": check,
        "backup": backup_check,
        "runtime_trace": trace,
        "runtime_metrics": {k: v for k, v in metrics.items() if k != "audit_snapshots"},
        "checks": checks,
        "passed": bool(checks) and all(checks.values()),
    }
    report_path = root / f"gate-{gate.lower()}-evidence.json"
    atomic_json(report_path, report)
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        raise RuntimeError(f"Gate {gate} blocked; failed checks: {failed}. Report: {report_path}")
    append_event(root, "gate_approved", {"gate": gate, "evidence_file": report_path.name,
                 "evidence_sha256": sha256_file(report_path), "checks": checks})
    next_phase = {"PREFLIGHT": "STABILITY", "STABILITY": "AUTONOMY", "AUTONOMY": "OFFICIAL"}[gate]
    state = load_state(root)
    state["phase"] = next_phase
    state["phase_started_at_utc"] = utc_now()
    if next_phase == "OFFICIAL":
        state["official_started_at_utc"] = utc_now()
        state["official_ends_at_utc"] = datetime.now(timezone.utc).timestamp() + 30 * 86400
    atomic_json(root / STATE, state)
    append_event(root, "phase_started", {"phase": next_phase, "official_clock_started": next_phase == "OFFICIAL"})
    print(json.dumps({"approved_gate": gate, "next_phase": next_phase,
                      "official_clock_started": next_phase == "OFFICIAL", "evidence_file": str(report_path)}, indent=2))



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
            approve_gate(args.run_dir, args.gate)
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
