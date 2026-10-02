# ISAAC — Master Plan (Konsolidierter Ist-Stand + Roadmap)

**Stand:** 2026-10-02
**Code-Basis:** `main` @ `4830737` (Merge PR #27, Jules-Intent-Fix)
**Umfang des Audits:** 698 Dateien · 126 Python-Module im Root (~58 000 Zeilen) · 31 Testmodule (~479 Tests) · `docs/` · Checklisten · offene GitHub-PRs · CI-Runs

> **Priorität bei Widersprüchen (unverändert):**
> `AGENTS.md` → `06_goal_autonomy_checklist.txt` / `05_evolution2_checklist.txt` → `docs/MASTER_ROADMAP_ISAAC_v5_2026-07-24.md` → **dieses Dokument** → Drive/PDF-Material
>
> Dieses Dokument **ersetzt keine** Leitdatei. Es gleicht die bestehenden Roadmaps mit dem **realen Code- und GitHub-Zustand** ab und listet, was tatsächlich noch offen ist.

---

## 1. Methodik

1. Alle offenen Checkbox-Punkte (`- [ ]`, `[!]`, `❌`, „offen“) in `*.md` / `*.txt` gesammelt.
2. Jeden Punkt im Code verifiziert (Grep auf Implementierung + Tests). Viele Roadmap-Punkte sind **im Code bereits erledigt**, aber in den Docs noch nicht abgehakt.
3. Python-Code nach `TODO` / `FIXME` / `XXX` / `HACK` / `NotImplementedError` durchsucht → **0 Treffer** (der Code ist sauber, offene Arbeit steht ausschließlich in Docs/PRs).
4. GitHub geprüft: offene PRs, Issues, CI-Runs.

---

## 2. Executive Summary

| Bereich | Status |
|---------|--------|
| Phasen 1–4, Evolution 2.0, Goal-Autonomie S0–S4 | ✅ abgeschlossen |
| Native Coding (`repo_map` / `code_edit` / `git_ops`) | ✅ |
| Track C1–C4 (Trace, MCP, Checkpoint, Self-Model) | ✅ |
| Ops T0.2 (Ollama-Sentry-Filter) und T1 (Follow-up-Kontinuität) | ✅ **im Code erledigt**, Docs nicht nachgezogen |
| CI (GitHub Actions) | ✅ **läuft wieder** (Python-Package, CodeQL, Remote-Smoke grün) — Billing-Lock ist aufgehoben, Docs sagen noch das Gegenteil |
| Offene PRs | 🔴 **6 offen**, 2 davon mit Merge-Konflikten, mehrere überlappen sich |
| Docs-Drift | 🟡 Eval-Zahl inkonsistent (README 130/130, Roadmap 96/96, E2-Checklist 66/66) |
| Code-TODOs | ✅ keine |

**Kernaussage:** Die größte offene Arbeit liegt **nicht** in neuem Code. Sie liegt in (a) der **Entscheidung über 6 offene Jules-PRs** und (b) einem **Doc-Sync**, damit die Roadmaps wieder die Wahrheit sagen.

---

## 3. Liste aller offenen Punkte (verifiziert)

Legende: **Kat.** = System-Taxonomie A–E (`docs/SYSTEM_TAXONOMY.md`)

### 3.1 Offene Pull Requests (höchste Priorität)

| PR | Titel | Zustand | Kat. | Bewertung |
|----|-------|---------|------|-----------|
| **#28** | Deepen *Prove the Kernel* runtime integration | mergeable, +167/−114, 4 Dateien, CI grün | A | Kandidat zum Merge nach Review. Baut auf #26 auf. |
| **#26** | Feature/prove the kernel | mergeable, **0 Dateien Diff** | — | **Leer**, also schon in main enthalten. → schließen |
| **#21** | DIVA modulators decay logic + state persistence | **CONFLICTING**, +1119/−3, 7 Dateien | A | Überlappt mit #19. Ändert `monitor_server.py` (REST), betrifft also auch D. |
| **#19** | DIVA runtime modulator (memory + strategy) | mergeable, +272/−4, 4 Dateien | A | Greift in `build_retrieval_context` ein, berührt Prinzip 2 (Retrieval vor Strategy). Genaues Review nötig. |
| **#17** | TaskGraph + causal DecisionTrace | **CONFLICTING**, +403/−10, 5 Dateien | A | `task_graph.py` gibt es auf main nicht. Möglicherweise durch *Prove the Kernel* (#28) überholt. Abgleich mit `docs/PROVE_THE_KERNEL.md §2`. |
| **#14** | Configure Vercel dashboard deploy | mergeable, +74/−1, 4 Dateien | B/D | Fällt unter die Do-NOT-Regel für Deploy/UI. Nur mit expliziter Freigabe durch dich. |

**Offene Fragen an den Owner:**
- DIVA: **ein** Modulator-Pfad (#19 *oder* #21), nicht beide.
- TaskGraph: #17 neben *Prove the Kernel* ist eine mögliche Doppelwahrheit, also dasselbe Anti-Muster wie die abgelehnte Drive-`task_state_machine`.

### 3.2 Track C — Consolidate

| ID | Punkt | Quelle | Ist-Stand | Aktion |
|----|-------|--------|-----------|--------|
| C5.1 | GitHub Actions Billing entsperren | Master v5 §5 | ✅ **erledigt** (Runs vom 2026-10-01/02 grün) | Docs abhaken |
| C5.2 | CI grün dokumentieren | Master v5 §5, §11 | 🟡 CI ist grün, aber nicht dokumentiert | Badge oder Eintrag in README |
| E2.0.5.4 | `[!]` Billing-Lock | `05_evolution2_checklist.txt` | ✅ erledigt | `[!]` → `[x]` |
| C1+ | `gen_ai.*`-Token-Felder aus Relay anreichern | Master v5 §3.1 | 🟡 Aliase vorhanden, Relay-Anreicherung offen | klein, optional |
| C4+ | Reflexion-Loop an Eval-Pass-Rate koppeln | Master v5 §3.4 | 🟡 Module da, keine Messkopplung | bounded, nach PR-Bereinigung |
| C2+ | MCP SDK-v1-Parität / mehr Contract-Tests | Master v5 §3.2 | 🟡 | optional |

### 3.3 Track G — Goal- und Owner-Autonomie

| ID | Punkt | Ist-Stand | Aktion |
|----|-------|-----------|--------|
| G1 | Live-Ops: Intervalle/Env in `OWNER_COMMANDS.md` pflegen | 🟡 offen | Env-Tabelle (`GOAL_AUTONOMY_INTERVAL`, `ISAAC_GOAL_SUBGOAL_COOLDOWN_S`, `ISAAC_GOAL_MAX_SUBGOAL_ATTEMPTS`) ergänzen |
| G2 | Status-Inspectability von `owner_autonomy` in Docs/Status-Block prüfen | 🟡 offen | `autonomy_status()` mit Doku abgleichen |

### 3.4 Track M — Memory (bounded)

| ID | Punkt | Ist-Stand | Aktion |
|----|-------|-----------|--------|
| M2 | Eval-Metriken für `forgetting_decay` | 🟡 optional offen | Decay-Case in `evals/learning_eval.py` |

### 3.5 Ops-Roadmap 2026-07-26 (T0–T3)

| ID | Punkt | Ist-Stand |
|----|-------|-----------|
| T0.1 | Sentry-Issues ISAAC-1/2/3/4/5/7/8/A/B resolven | ⚪ nicht verifizierbar ohne Sentry-Zugriff (Owner, UI/API) |
| T0.2 | ISAAC-9 Ollama dämpfen | ✅ `isaac_sentry._before_send` + Test `test_before_send_drops_ollama_noise_when_free_cloud` |
| T0.3 | ISAAC-6 Volumen-Anomalie diagnostizieren | ⚪ offen (Owner/Sentry) |
| T0-DoD | `docs/SENTRY.md` Hygiene-Absatz | ✅ vorhanden (`SENTRY.md:102`) |
| T1 | Follow-up „Und?“ ohne Credential-Fishing | ✅ `isaac_core._is_short_followup` + `test_followup_und_continuity_no_credential_fishing` |
| T1-DoD | Live-Sequenz C→G lokal verifizieren | ⚪ manueller Live-Check offen |
| T2 | Ein Browser-`goto` lokal mit `evidence-ok`, Creds nie in URL | ⚪ offen (lokal, Playwright) |
| T3.b | `ISAAC_WS_URL` in `remote_smoke` | 🟡 nicht gefunden, offen |
| T4 | Dashboard 6.1 | ⛔ nur bei konkretem Bug oder Owner-Ticket |

### 3.6 Security-Checkliste (`docs/CONNECTIONS_AND_SECRETS.md`)

Dauerhafte Owner-Pflichten, kein Code:
- [ ] Keys rotieren, die je in einen Chat kopiert wurden
- [ ] Least-Privilege-GitHub-Tokens
- [ ] Render-Secrets nur im Dashboard

### 3.7 Docs-Drift (Wahrheit ≠ Dokumentation)

| Datei | Problem |
|-------|---------|
| `README.md` | Eval **130/130** (aktuellster Wert, als Referenz nehmen) |
| `docs/MASTER_ROADMAP_ISAAC_v5_2026-07-24.md` | sagt **96/96** und „CI Billing offen“ |
| `05_evolution2_checklist.txt` | sagt **66/66**, `[!] 5.4` Billing |
| `docs/ROADMAP_OPS_2026-07-26.md` | T0.2/T1 als offen, obwohl erledigt |
| `ANDROID_ADMIN_MODE.md:144–147` | „Learning-Loops / Inquiry nicht gebaut“, ist **falsch**: Inquiry (`goal_inquiry`) und Learning (`learning_engine`, `learning_policy`) existieren |
| `AGENTS.md` Struktur-Tabelle | neue Module fehlen: `integrations/jules.py`, `integrations/browserbase.py`, `diva_protocol.py`, `self_reflection_policy.py` |

### 3.8 Repo-Hygiene

| Punkt | Bemerkung |
|-------|-----------|
| `web/` (next-forge-Monorepo, ~20 Packages) | Unbenutztes Boilerplate (Kat. D), das keinen Kernel-Pfad nutzt. Entscheidung: behalten, auslagern oder löschen. |
| `openapi_letta.json` | Laut Ops-Roadmap „nicht ohne Review committen“, inzwischen getrackt. Prüfen, ob generiert. |
| `.github/instructions/*.pdf` | Research-Material (SNN/WBE), korrekt als Track R markiert. Nicht anfassen. |

### 3.9 Bewusst geparkt (Do-NOT, kein offener Punkt)

Human Layer, Personality, Trust-Modeling gegen Owner, Dashboard-Redesign, Vector-Memory-Redesign, MCP-Subagenten, LangGraph/CrewAI/Aider wholesale, SNN/WBE auf main (Track R).
Diese Punkte sind **keine Lücken**, sondern Architekturentscheidungen (`AGENTS.md`, Master v5 §8).

---

## 4. Roadmap

Jede Stufe ist klein, testbar und nach jedem Schritt lauffähig. Validierung siehe §6.

### Stufe 0 — Aufräumen und Wahrheit herstellen (sofort, kein Kernel-Risiko)

| # | Arbeit | Kat. | DoD |
|---|--------|------|-----|
| 0.1 | PR **#26** schließen (leer) | — | geschlossen |
| 0.2 | Docs-Sync: Billing/CI abhaken, Eval-Zahl vereinheitlichen, T0.2/T1 abhaken, `ANDROID_ADMIN_MODE.md` korrigieren | E/Doku | alle Leitdateien sagen dasselbe |
| 0.3 | `AGENTS.md` Struktur-Tabelle um Jules/Browserbase/DIVA/Self-Reflection ergänzen | Doku | Tabelle = Dateisystem |
| 0.4 | CI-Status in README dokumentieren | E | C5 DoD erfüllt |

### Stufe 1 — PR-Entscheidungen (Kernel-relevant, Review-pflichtig)

| # | Arbeit | Kat. | DoD |
|---|--------|------|-----|
| 1.1 | **#28** Prove-the-Kernel reviewen, lokal `unittest` + `eval_runner` ausführen, mergen | A | Evals ≥ 130, keine Regression |
| 1.2 | **#17** TaskGraph gegen Prove-the-Kernel-TaskGraph abgleichen. Bei Redundanz schließen, sonst rebasen | A | **ein** TaskGraph-Modell |
| 1.3 | **DIVA:** #19 vs #21 entscheiden. Empfehlung: #19 (kleiner, mergeable) als Basis, Decay aus #21 gezielt nachziehen | A | ein Modulator, Retrieval vor Strategy bleibt gewahrt |
| 1.4 | **#14** Vercel-Deploy: nur mit Owner-Freigabe (Kat. B/D) | B/D | bewusste Entscheidung |

### Stufe 2 — Restliche Konsolidierung (bounded)

| # | Arbeit | Kat. | DoD |
|---|--------|------|-----|
| 2.1 | G1: Goal-Env-Tabelle in `OWNER_COMMANDS.md` | Doku | Env vollständig |
| 2.2 | G2: `autonomy_status()` mit Status-Block und Docs abgleichen | A/C | inspectable |
| 2.3 | T3.b: `ISAAC_WS_URL` in `remote_smoke.py` | E | lokal und remote testbar |
| 2.4 | M2: Decay-Eval in `learning_eval` | E | neue Eval grün |
| 2.5 | C1+: Relay-Token-Anreicherung `gen_ai.usage.*` | C | portable Export enthält Tokens |

### Stufe 3 — Messbare Selbstverbesserung (bounded, nach Stufe 1)

| # | Arbeit | Kat. | DoD |
|---|--------|------|-----|
| 3.1 | Reflexion-Loop an Eval-Pass-Rate koppeln (Prove-the-Kernel §5 Metriken) | A | Metrik im Trace, bounded via `learning_policy` |
| 3.2 | 100-Task-E2E-Benchmark (`evals/tasks_100_e2e.json`) regelmäßig laufen lassen und Snapshot versionieren | E | Trend sichtbar |
| 3.3 | Epistemisches Memory (Prove-the-Kernel §4) in `build_retrieval_context` sichtbar machen, **ohne** zweiten Retrieval-Pfad | A | ein Retrieval-Pfad |

### Stufe 4 — Owner-Ops (nicht durch Agenten lösbar)

- T0.1 / T0.3 Sentry-Issues resolven oder diagnostizieren
- T1-Live-Check C→G, T2 Browser-E2E lokal
- Secrets rotieren, Least-Privilege-Tokens
- Entscheidung über `web/` und `openapi_letta.json`

### Track R — Research Brain (geparkt)

Unverändert: nur mit expliziter Owner-Freigabe, isoliertem Branch und Feature-Flag (Master v5 §5 Track R).

---

## 5. Abhängigkeiten

```text
Stufe 0 (Docs/PR #26) ──► saubere Basis
Stufe 1.1 (#28) ──► 1.2 (#17 Abgleich) ──► 3.3 (epistemisches Memory)
Stufe 1.3 (DIVA) ──► 3.1 (Reflexion/Metriken)
Stufe 2 parallel zu Stufe 1 möglich
Stufe 4 jederzeit (Owner)
Track R ⛔ bis explizite Freigabe
```

---

## 6. Validierung (Pflicht je Schritt)

```bash
python3 -m py_compile isaac_core.py executor.py low_complexity.py memory.py relay.py logic.py \
  watchdog.py task_checkpoint.py decision_trace.py mcp_server.py mcp_registry.py \
  repo_map.py code_edit.py git_ops.py
ISAAC_DISABLE_VECTOR_MEMORY=1 python3 sanity_check.py
ISAAC_DISABLE_VECTOR_MEMORY=1 python3 -m unittest \
  tests_phase_a_stabilization tests_state_io tests_provider_configuration \
  tests_repo_map tests_code_edit tests_git_ops -q
ISAAC_DISABLE_VECTOR_MEMORY=1 python3 -m evals.eval_runner
```

---

## 7. Definition of Done (Master Plan)

- [ ] Offene PRs: jeder PR gemergt oder begründet geschlossen
- [ ] Ein TaskGraph-Modell, ein DIVA-Modulator, ein Retrieval-Pfad
- [ ] Alle Leitdateien nennen dieselbe Eval-Zahl und denselben CI-Status
- [ ] G1/G2/M2/T3.b erledigt
- [ ] Reflexion messbar an Eval-Pass-Rate gekoppelt (bounded)
- [ ] Research-Brain weiterhin nicht mit Kernel-main vermischt

---

*Isaac Kernel v5.3 · Master Plan · 2026-10-02 · erstellt aus Code-Audit, Leitdateien, Checklisten und GitHub-Zustand.*
