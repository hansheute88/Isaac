# Isaac — File-Level Provenance Matrix

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`  
**Purpose:** technical/IP diligence and provenance classification.  
**Important:** this is a project provenance classification, not a legal opinion on copyrightability.

## 1. Classification key

| Code | Meaning | Acquisition treatment |
|---|---|---|
| **H1** | Hans Heute — conceptual/theoretical/architectural material | Core founder-originated project asset |
| **H2** | Hans-directed implementation, with AI coding assistance | Isaac implementation; retain AI-assistance provenance; do not imply line-by-line human authorship without evidence |
| **H3** | Hans-directed project documentation / tests / operational material, AI-assisted where applicable | Project asset; classify individual third-party passages separately |
| **T1** | Third-party / template-derived source | Not exclusive Isaac IP; preserve applicable license/notice |
| **T2** | Third-party dependency / lockfile / generated dependency metadata | Not exclusive Isaac IP |
| **G1** | Generated/build/deployment artifact | Generally not an exclusive conceptual asset; retain provenance |
| **U1** | Unresolved / requires file-level comparison | Conservative treatment: do not claim exclusively proprietary |
| **MIX** | Mixed provenance within a file/tree | Split or annotate before transaction; do not make blanket ownership claim |

## 2. Repository-wide inventory snapshot

The acquisition-readiness branch currently contains **876 tracked tree entries**.

| Tree area | Files | Initial treatment |
|---|---:|---|
| `web/` | 423 | **T1/U1** until file-level next-forge comparison is complete |
| `docs/` | 42 | **H1/H3**, with third-party excerpts/links reviewed separately |
| `evals/` | 17 | **H3/H2** |
| `external_memory/` | 12 | **H2/T1 MIX**; adapter code vs upstream/provider material must be separated |
| `.github/` | 12 | **H3/T1 MIX**; agent instructions are project material, embedded PDFs require provenance review |
| `scripts/` | 20 | **H2/H3**, except scripts demonstrably copied from upstream |
| `tests/` + root `tests_*.py` | 6 + root test files | **H3/H2**; third-party fixtures/examples require review |
| remaining runtime / config / deployment trees | remainder | classify by module matrix below |

The repository-wide count is an inventory baseline, not a statement that every tracked file is copyright-protected or exclusively owned by the project owner.

## 3. Isaac cognitive kernel — primary proprietary implementation boundary

These modules are the strongest candidates for **H2** (Hans-directed Isaac implementation with AI coding assistance), because they implement the project-specific cognitive/control architecture documented by the repository.

### Core orchestration and cognition

- `isaac_core.py`
- `low_complexity.py`
- `dispatcher.py`
- `decomposer.py`
- `decomposer_adaptive.py`
- `logic.py`
- `execution_contract.py`
- `result_contract.py`
- `executor.py`

**IP significance:** very high. These files implement the repository's explicit classification → retrieval → strategy → task → execution → evaluation → memory model.

### Memory, knowledge and learning

- `memory.py`
- `vector_memory.py`
- `procedure_memory.py`
- `forgetting_decay.py`
- `meaning.py`
- `values.py`
- `value_decisions.py`
- `learning_engine.py`
- `learning_policy.py`
- `reflection.py`
- `instincts.py`
- `neural_core.py`

**IP significance:** high. These are implementation mechanisms corresponding to the project's memory, learning, reflection, values and development model.

### Goal-directed autonomy

- `goal_store.py`
- `goal_inquiry.py`
- `goal_digest.py`
- `motivation.py`
- `owner_autonomy.py`
- `owner_action.py`

**IP significance:** very high. This is a distinctive project-specific control model for owner-aligned goals, subgoals, motivation, confirmation, cooldowns and bounded autonomy.

### Governance, identity and safety

- `constitution.py`
- `constitution_override.py`
- `privilege.py`
- `sudo_gate.py`
- `regelwerk.py`
- `security_policy.py`
- `security_toolkit.py`
- `security_workflows.py`
- `self_model.py`
- `self_model_hooks.py`
- `self_reflection_policy.py`
- `trust_engine.py`

**IP significance:** very high. The project-specific governance/control model is a central differentiator.

## 4. Execution and environment-control implementation

Initial classification: **H2**, subject to third-party/API-specific review.

- `tool_registry.py`
- `tool_catalog.py`
- `tool_policy.py`
- `tool_runtime.py`
- `tool_bridge.py`
- `task_tool_state.py`
- `computer_use.py`
- `ui_automation.py`
- `windows_desktop.py`
- `file_access.py`
- `credential_access.py`
- `browser.py`
- `browser_chat.py`
- `chrome_tabs.py`
- `chrome_secrets.py`
- `android_apps.py`
- `termux_bridge.py`
- `s8_remote/`

These are Isaac implementation components, but individual API integrations, protocol implementations and copied examples must remain subject to their respective terms/licenses.

## 5. Native coding / self-development subsystem

Initial classification: **H2**.

- `repo_map.py`
- `code_edit.py`
- `git_ops.py`
- `updater.py`
- `task_checkpoint.py`

**IP significance:** high. The repository explicitly defines a bounded, inspectable code-development mechanism rather than wholesale import of an external coding agent.

The repository itself prohibits:
- wholesale Aider/OpenHands/Cline imports;
- fuzzy application of ambiguous edits;
- chat-to-repository writes;
- force-push/history rewriting;
- unbounded automatic commits.

## 6. Provider / relay / agent integration layer

Initial classification: **H2/T1 MIX**.

- `relay.py`
- `free_cloud.py`
- `openrouter_ensemble.py`
- `agent_selection.py`
- `hermes_compat.py`
- `isaac_remote.py`
- `ki_skills.py`
- `mcp_client.py`
- `mcp_integration.py`
- `mcp_jsonrpc.py`
- `mcp_registry.py`
- `mcp_server.py`
- `agents/isaac_mcp_agent.py`
- `integrations/`

The Isaac-specific orchestration/adaptation code can be project IP; provider SDKs, protocol specifications, examples and copied implementation fragments remain third-party.

## 7. MCP boundary

Initial classification: **H2**, with protocol/SDK material separately licensed where applicable.

- `mcp_client.py`
- `mcp_server.py`
- `mcp_registry.py`
- `mcp_jsonrpc.py`
- `mcp_integration.py`
- `agents/isaac_mcp_agent.py`

The project-specific governance at the MCP boundary — including origin/method/name/version validation and blocking of unsafe remote write/override operations — is part of the Isaac implementation.

## 8. Observability and evidence layer

Initial classification: **H2/H3**, with external SDK portions treated as T2.

- `audit.py`
- `decision_trace.py`
- `isaac_sentry.py`
- `watchdog.py`
- `monitor_api.py`
- `monitor_now.py`
- `monitor_server.py`
- `traces/`

Sentry SDK code itself is third-party; Isaac's integration, event model and project-specific trace semantics are separate.

## 9. Configuration, state and secrets

Initial classification: **H2/H3**, with generated/secrets material separated.

- `config.py`
- `isaac_startup_config.py`
- `state_io.py`
- `secrets_store.py`
- `secrets_bootstrap.py`
- `security_policy.py`

Do not treat actual credentials, local runtime databases, generated state or provider secrets as transferable source IP.

## 10. UI and presentation

### Local UI

Initial classification: **H2/H3** where Isaac-specific:

- `dashboard.html`
- `browser_chat.py`
- `ki_dialog.py`
- `monitor_server.py`

### `web/`

Initial classification: **T1/U1/MIX**, not exclusive Isaac IP.

The web workspace explicitly identifies itself as **next-forge 6.0.2** and points to the Vercel next-forge repository. It therefore remains outside the exclusive-IP boundary until every file is compared against the corresponding upstream release.

Required final file-level labels for `web/`:

- `[THIRD-PARTY]`
- `[MODIFIED THIRD-PARTY]`
- `[ISAAC-ORIGINAL]`
- `[AI-ASSISTED ISAAC]`
- `[GENERATED]`

See `docs/WEB_PROVENANCE.md`.

## 11. Tests, evaluations and security harnesses

Initial classification: **H3/H2**.

- `evals/`
- root `tests_*.py`
- `tests/`
- `remote_smoke.py`
- `sanity_check.py`
- `bug_bounty.py`

These are valuable evidence of engineering provenance and validation. They should not be presented as independent proof of scientific claims.

## 12. Documentation and theory traceability

Initial classification:

- **H1:** project theory and conceptual architecture
- **H3:** project-specific operational documentation
- **T1/U1:** copied external documentation, templates or embedded third-party works

High-value files include:

- `AGENTS.md`
- `README.md`
- `05_evolution2_checklist.txt`
- `06_goal_autonomy_checklist.txt`
- `docs/EVOLUTION2_TRACEABILITY.md`
- `docs/SYSTEM_TAXONOMY.md`
- `docs/MASTER_ROADMAP_ISAAC_v5_2026-07-24.md`
- `docs/LEITBILD.md`
- `docs/IP_AND_THIRD_PARTY.md`
- `docs/AI_CODE_PROVENANCE.md`
- `docs/IDENTITY_AND_PROVENANCE.md`

Embedded PDFs and imported research documents under `.github/instructions/` require individual provenance review before being included in an exclusive-IP package.

## 13. Dependency and generated metadata boundary

Treat the following as **T2/G1**, not exclusive Isaac IP:

- `requirements.txt`
- `requirements-memory-extra.txt`
- `web/pnpm-lock.yaml`
- package-manager generated metadata
- build output
- deployment manifests copied from external templates
- provider SDK source/bundled runtime

The project's own dependency declarations and integration decisions remain project evidence, but the underlying packages are separately licensed.

## 14. Explicit next-forge boundary

Current evidence establishes:

- `web/package.json` is named `next-forge`;
- version is `6.0.2`;
- repository points to `vercel/next-forge`;
- `web/README.md` identifies next-forge as the template and states MIT licensing.

Therefore:

**Do not claim the entire `web/` tree as Hans-original Isaac IP.**

The clean transaction boundary is:

**Isaac cognitive/control kernel + Isaac-specific integrations**  
vs.  
**template-derived web/presentation/infrastructure layer**

## 15. What this matrix does NOT establish

This matrix does not establish:

1. legal copyrightability of AI-generated code;
2. ownership of every individual generated line;
3. absence of third-party snippets in runtime files;
4. absence of patent claims by third parties;
5. complete dependency license compliance;
6. complete historical secret/provenance audit;
7. scientific validation of Evolution 2.0.

Those require separate diligence.

## 16. Required next diligence steps

1. **File-level next-forge diff** for every tracked file under `web/`.
2. **Dependency license enrichment** for Python and npm/pnpm dependency closure.
3. **Historical provenance scan** of Git blobs/diffs, including deleted files.
4. **Third-party snippet scan** across runtime source.
5. **Embedded-document provenance review** under `.github/instructions/` and similar directories.
6. **Runtime identifier cleanup** for the internal `Steffen` identifier, without changing behavior on this acquisition branch.
7. **Owner evidence package:** retain private evidence linking historical GitHub identities to Hans Heute and showing project-direction decisions.
8. **Transaction-ready manifest:** produce a final file list with one of the labels H1/H2/H3/T1/T2/G1/U1/MIX.

## 17. Bottom line

The strongest proprietary asset is not a dependency, web template or single Python file. It is the **system-level combination**:

**Mensch & KI / Evolution 2.0 conceptual framework  
→ Isaac architecture  
→ governance and controlled autonomy  
→ persistent/provenance-aware memory  
→ bounded execution and computer control  
→ bounded self-development  
→ audit/evaluation evidence**

That chain should be the center of technical/IP diligence.
