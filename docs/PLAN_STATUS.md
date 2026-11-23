# Isaac — Plan-Status (Single Source of Truth)

Stand: nach der Integration von `isaac-2.0/masterplan` in `main`
(Branch `isaac-2.0/integration` → PR → `main`).

Diese Matrix ersetzt keine der Plandokumente, sondern sagt für jeden Planpunkt, **wo der
Code liegt und womit er belegt ist**. Grundsatz (AGENTS.md): kein „done" ohne Datei/Test/Artefakt.

Legende: ✅ umgesetzt & getestet · ⏸ bewusst zurückgestellt · ⏳ Owner-Aufgabe (Konto/Hardware)
· 🚫 per AGENTS.md ausgeschlossen.

## 1. Isaac 2.0 Masterplan (Tracks A–H)

| Track | Status | Evidenz |
|---|---|---|
| A — Architecture Contract | ✅ | `docs/ISAAC_2.0_MASTERPLAN.md`, `docs/ISAAC_2.0_A0_BASELINE.md`, `docs/ISAAC_2.0_B2_CAPABILITY_CONTRACT.md`, `docs/ISAAC_2.0_B3_CAUSAL_EVENT_SCHEMA.md` |
| B — R/W/X Capability | ✅ | `isaac_capabilities.py`; Enforcement am Tool-Boundary in `tool_runtime.py`; `tests_isaac20_capabilities.py`, `tests_isaac20_e2e.py` |
| C — Causal Memory | ✅ | `isaac_causal.py`, `isaac_causal_query.py`; lineage via `audit.py`/`decision_trace.py`; `tests_isaac20_causal.py`, `tests_isaac20_causal_query.py`, `tests_isaac20_runtime_lineage.py` |
| D — Cybernetic Guardrail | ✅ | `isaac_guardrails.py`, `watchdog.py`, `relay.py`; Quarantäne/Recovery-Lifecycle; `tests_isaac20_guardrails.py` |
| E — Metrics & Benchmarks | ✅ | `benchmarks/isaac20_fault_injection.py` (E1), `benchmarks/isaac20_metrics.py` (E2), `benchmarks/isaac20_ablation.py` (E3); `tests_isaac20_e1/e2/e3.py`; CI-Job `isaac20` |
| F — Governance Evidence | ✅ | `benchmarks/isaac20_governance.py` (F1), `benchmarks/isaac20_governance_f2.py` (F2); `tests_isaac20_f1.py`, `tests_isaac20_f2.py` |
| G — SDK / CLI | ✅ SDK / ⏸ CLI | `isaac_sdk.py`, `tests_isaac20_sdk.py`; CLI (§14) bewusst zurückgestellt — nur dokumentiert |
| H — Investor Demo | ✅ | `benchmarks/isaac20_investor_demo.py`, `tests_isaac20_investor_demo.py` |
| §15 Dashboard-Views | ⏸ | Zurückgestellt (AGENTS.md: keine Dashboard-/UI-Expansion ohne Owner-Ticket) |

## 2. Isaac 30-Day Autonomy Contract

| Baustein | Status | Evidenz |
|---|---|---|
| Decision-Cycle-Evidenz | ✅ | `isaac_autonomy_cycle.py`, `isaac_autonomy_reconstruction.py`, `isaac_autonomy_verification.py`; `tests_isaac_autonomy_*.py` |
| Learning-Causality | ✅ | `isaac_learning_causality.py`; `tests_isaac_learning_causality.py` |
| Bounded Interests | ✅ | `isaac_interest_derivation.py`; `tests_isaac_interest_derivation.py` |
| Runtime-Audit-Hooks | ✅ | `isaac_runtime_audit.py`, `isaac_governance_gate.py`; `tests_isaac_runtime_audit.py`, `tests_isaac_governance_gate.py` |
| Evidence-Ledger | ✅ | `isaac_30day_evidence.py`, `scripts/verify_isaac_30day_evidence.py`; `tests_isaac_30day_evidence.py` |
| Supervisor/Launcher | ✅ | `scripts/start_isaac_30day_proof.ps1` (Runbook: `docs/ISAAC_30DAY_PROOF_RUNBOOK.md`) |
| Offizieller 30-Tage-Lauf | ⏳ | 30 Tage Windows-11-Hardware, Gated 24h/48h/72h; nicht Teil dieses Plans |

## 3. Master Roadmap v5

| Punkt | Status | Evidenz |
|---|---|---|
| C1 Observable DecisionTrace | ✅ | `decision_trace.py` (portable export, EXECUTION-Metadaten) |
| C2 MCP-Härtung | ✅ | `mcp_server.py`, `mcp_registry.py`, `evals/mcp_eval.py`, `docs/MCP_CAPABILITY.md` |
| C3 Checkpoint/Resume | ✅ | `task_checkpoint.py`, `evals/replay_eval.py` |
| C4 Self-Model/Learning bounded | ✅ | `self_model_hooks.py`, `learning_policy.py`, `evals/identity_eval.py`, `evals/learning_eval.py` |
| C5 CI grün | ⏳ | GitHub-Billing/CI-Runs liegen beim Owner |
| G1 Goal-Autonomie Live-Ops | ✅ | Env-Tabelle in `docs/OWNER_COMMANDS.md` (Goal-Autonomie) |
| G2 Owner-Autonomie-Status | ✅ | `owner_autonomy.autonomy_status()`, `isaac status`, `tests_phase_a_stabilization` |
| M1 Memory-Adapter fail-soft | ✅ | `external_memory/*`, `vector_memory.py`, `tests_external_memory.py` |
| M2 Decay-Metriken | ⏸ | optional laut Roadmap; kein Code, `forgetting_decay.py` bleibt unverändert |
| R Research Brain (SNN/WBE) | 🚫 | geparkt, nur mit Owner-Freigabe |

## 4. Ops-Roadmap 2026-07-26

| Item | Status | Evidenz |
|---|---|---|
| T0.2 ISAAC-9 Ollama-Dämpfung | ✅ | `isaac_sentry._before_send`, `relay.py`; `tests_sentry_ai_monitoring.py` |
| T0.1 / T0.3 Sentry-Items | ⏳ | braucht Sentry-Zugang (Owner) |
| T1 Follow-up-Continuity | ✅ | `isaac_core._is_short_followup`, `_strip_mission_noise_from_context`, Strategy-Note; `test_followup_und_continuity_no_credential_fishing` |
| T2 Browser-E2E | 🔶 | `tests_browser_live_playwright.py` lokal; keine Credentials in CI |
| T3.a Remote-Smoke-Runs | ⏳ | read-only manuell |
| T3.b `ISAAC_WS_URL` | ✅ | `remote_smoke.configured_ws_url()`, `tests_isaac_remote.py`; `docs/ISAAC_REMOTE.md`, `docs/OWNER_COMMANDS.md` |
| T4 Dashboard | 🚫 | nur blockierende Bugs / Owner-Ticket |
| T5 glinka / T6 Secrets | ⏳ | Owner |

## 5. Prove the Kernel (5 Säulen)

| Säule | Status | Evidenz |
|---|---|---|
| 1 E2E-Benchmark (100 Tasks) | ✅ | `evals/kernel_benchmark.py`, `evals/tasks_100_e2e.json`, `evals/eval_runner.py` |
| 2 TaskGraph-Modell | ✅ | `executor.Task` (dependencies/goal/evidence/decision_trace), `evals/replay_eval.py` |
| 3 Learning-Commit-Pipeline | ✅ | `learning_engine.py`, `learning_policy.py`, `evals/learning_eval.py` |
| 4 Epistemisches Memory | ✅ | `memory.py` (`EpistemicClass`, `add_epistemic_memory`), `tests_prove_the_kernel.py` |
| 5 Autonomie-/Governance-Metriken | ✅ | `evals/kernel_metrics.py`, `tests_prove_the_kernel.py` |

## 6. Nicht Teil dieses Plans

- Masterplan §14 (CLI) und §15 (Dashboard-Views) — nur dokumentiert.
- Offizieller 30-Tage-Proof-Lauf, Sentry-Item-Auflösung, CI-Billing-Entsperrung (Owner).
- `web/`-Monorepo (next-forge) — unberührt.
