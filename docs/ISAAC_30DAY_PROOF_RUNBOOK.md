# Isaac 30-Day Proof Runbook (Windows 11)

## Status and safety

This is the **preparation and evidence supervisor**, not a claim that the official proof run has started or passed. The official 30-day clock is unset until the supervisor observes the 24h, 48h, and 72h gates passing in sequence.

The launcher refuses to run unless:
- the checkout is on `isaac-2.0/masterplan`;
- the Git working tree is clean and the source revision can be pinned;
- the supervisor tests and Python compilation pass;
- the evidence directory is new; and
- the backup directory is on a different drive/root from the evidence directory.

It never changes `main`, does not fabricate test events, and does not overwrite an existing evidence run.

## Before starting

1. Merge the supervisor PR into `isaac-2.0/masterplan`, then update the Windows checkout to that branch and commit.
2. Ensure the Isaac virtual environment exists at `.venv\Scripts\python.exe`.
3. Choose an evidence directory and a backup location on a different physical drive or a separately managed network share. Ensure the backup target is protected against ordinary user edits.
4. Confirm Isaac's local health endpoint responds at `http://127.0.0.1:8766/`. Pass a different `-HealthUrl` if your configuration uses another endpoint.
5. Connect the PC to power and configure Windows not to sleep for the duration. The script deliberately does not change power settings on your behalf.

## Start

Open PowerShell in the repository and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\start_isaac_30day_proof.ps1 `
  -EvidenceDir "C:\IsaacProof\Evidence" `
  -BackupDir "D:\IsaacProofBackup"
```

Use a backup path on a separate drive or managed network share. The launcher starts `isaac_core.py`, waits for a successful local health probe, and then starts the supervisor in a separate background process. It sets `ISAAC_30DAY_EVIDENCE_DIR` and `ISAAC_30DAY_OFFICIAL=1` only for those processes.

## Gates and clock

- **24h preflight:** at least one real health sample, all observed health samples healthy, valid event hash chain, and continuous sampling.
- **48h stability:** 24h gate passed plus one cycle with linked authorization, execution, and evaluation evidence.
- **72h autonomy:** earlier gates passed, measurable schema-valid learning evidence, at least two valid bounded-interest derivations, zero recorded unauthorized executions/manual owner-goal mutations, and an explicit runtime `proof_audit_readiness` event covering every required execution and state-mutation surface.
- **Official 30 days:** begins only after the 72h gate passes. Final completion additionally requires at least 5 planner/inquiry/recovery-generated subgoals, 10 schema-valid research cycles, measurable downstream learning effects, zero unauthorized actions, zero manual mutations, and a valid evidence chain.

A health failure, backward clock movement, monitoring gap, event-chain tampering, unauthorized action, or recorded manual mutation fails the run closed. Preserve failed evidence for diagnosis; use a new directory for a new run.

## Evidence files

- `events.jsonl`: fsync'd hash-chained supervisor and runtime events.
- `run_state.json`: pinned source revision, gate state, official clock and failure state.
- `manifest.json`: SHA-256 and size metadata for the event ledger and run state.
- backup snapshots: regular copies of the ledger, state, and manifest.
- `supervisor.stdout.log` / `supervisor.stderr.log`: watcher process logs.
- `final_report.json`: candidate report after 30 days, before independent validation.
- `independent_validation.json`: detached independent verification result bound to the final manifest hash.

Verify at any time:

```powershell
.\.venv\Scripts\python.exe -m isaac_30day_evidence verify --evidence-dir "C:\IsaacProof\Evidence"
```

The hash chain detects changes made after events are recorded. It is not a substitute for access control or independent custody of the backup drive.

When the supervisor reports `AWAITING_INDEPENDENT_VALIDATION` after the 30-day criteria are met, run:

```powershell
.\\.venv\\Scripts\\python.exe -m isaac_30day_evidence finalize --evidence-dir "C:\\IsaacProof\\Evidence"
```

This finalization step changes the run to `COMPLETE` only if the separate standard-library verifier passes. It writes `independent_validation.json`, bound to the final manifest hash. If validation fails, the run is marked `FAILED_FINAL_VALIDATION`; preserve the entire evidence package.

## Known limitation before the official run

The gate is deliberately fail-closed. Runtime hooks record goal-autonomy cycle boundaries and the existing selection/authorization, task execution, and evaluation path. GoalStore subgoal creation, schema-valid learning records, and schema-valid interest derivations are recorded only when those real code paths execute. I have not established that the current production loop naturally produces the required causal learning records and two valid bounded-interest derivations end-to-end. More importantly, the current code does **not** yet emit a trustworthy `proof_audit_readiness` event proving coverage of all required surfaces (`executor_tools`, `owner_actions`, `browser_missions`, `mcp_tools`, `state_store_writes`, `filesystem_state`). Consequently, the 72h gate and official 30-day clock must remain blocked until that coverage is implemented and independently tested. Do not manually add readiness events or evidence to make a gate pass. If the 72h gate does not pass, treat that as a real integration/behavior gap to fix before attempting the official run.
