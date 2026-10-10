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

Use a backup path on a separate drive or managed network share. The launcher starts `isaac_core.py`, waits for a successful local health probe, binds the run to that process ID, and then starts the supervisor in a separate background process. Health samples verify both the local endpoint and the actual Isaac process. It sets `ISAAC_30DAY_EVIDENCE_DIR` and `ISAAC_30DAY_OFFICIAL=1` only for those processes.

## Gates and clock

- **24h preflight:** at least one real health sample, all observed health samples healthy, valid event hash chain, and continuous sampling.
- **48h stability:** 24h gate passed plus one cycle with linked authorization, execution, and evaluation evidence.
- **72h autonomy:** earlier gates passed, measurable schema-valid learning evidence, at least two valid bounded-interest derivations, zero recorded unauthorized executions/manual owner-goal mutations, and an explicit runtime `proof_audit_readiness` event covering every required execution and state-mutation surface.
- **Official 30 days:** begins only after the 72h gate passes. Final completion additionally requires at least 5 planner/inquiry/recovery-generated subgoals, 10 schema-valid research cycles, measurable downstream learning effects, zero unauthorized actions, zero manual mutations, and a valid evidence chain.

A health failure, backward clock movement, monitoring gap, event-chain tampering, unauthorized action, or recorded manual mutation fails the run closed. Preserve failed evidence for diagnosis; use a new directory for a new run.

## Evidence files

- `events.jsonl`: fsync'd hash-chained supervisor and runtime events.
- `run_state.json`: pinned source revision, gate state, official clock and failure state.
- `manifest.json`: SHA-256 and size metadata for the event ledger, run state, and final report.
- backup snapshots: regular copies of the ledger, state, manifest, final report, and independent validation when present.
- `supervisor.stdout.log` / `supervisor.stderr.log`: watcher process logs.
- `final_report.json`: candidate report after 30 days, before independent validation.
- `independent_validation.json`: detached independent verification result bound to the final manifest hash.

Verify at any time:

```powershell
.\.venv\Scripts\python.exe -m isaac_30day_evidence verify --evidence-dir "C:\IsaacProof\Evidence"
```

The hash chain detects changes made after events are recorded. It is not a substitute for access control or independent custody of the backup drive.

When the supervisor reports `AWAITING_INDEPENDENT_VALIDATION` after the 30-day criteria are met, stop the Isaac process cleanly first. The finalizer refuses to run while the recorded runtime PID is still alive, so the evidence package can be frozen. Then run:

```powershell
.\.venv\Scripts\python.exe -m isaac_30day_evidence finalize --evidence-dir "C:\IsaacProof\Evidence"
```

This finalization step changes the run to `COMPLETE` only if the separate standard-library verifier passes. It writes `independent_validation.json`, bound to the final manifest hash. If validation fails, the run is marked `FAILED_FINAL_VALIDATION`; preserve the entire evidence package.

## Runtime integration status before the official run

The runtime audit integration now instruments the existing production entry points for `executor_tools`, `owner_actions`, `browser_missions`, `mcp_tools`, `state_store_writes`, and `filesystem_state`. Kernel startup checks the concrete hook inventory and emits `proof_audit_readiness` only when every required hook is present. In official mode, missing hooks or evidence-write failures stop the affected path rather than silently claiming proof.

The existing research executor now records source references and a real evaluation event. Goal-driven research can emit a schema-valid causal learning record only when the task completed, source references were collected, and an evaluation exists. A bounded interest derivation is emitted only when the actual research response contains a recognizable follow-up/recommendation sentence and the active goal/subgoal IDs align. It records a proposal only and does not automatically mutate owner goals.

These are code and CI integration checks, **not proof that the target Windows 11 runtime has passed the gates**. Before the official run, CI must be green on the merged revision, and the actual Windows launcher, health endpoint, event ledger, hash chain, and independent backup must be validated. It is still unproven that normal production activity will naturally yield the required learning effects and at least two valid bounded-interest derivations. Therefore the 72h gate and official 30-day clock remain blocked until the real run provides those events. Do not manually add readiness events or evidence to make a gate pass. If a gate does not pass, treat that as a real integration/behavior gap to fix before attempting the official run.
