# Isaac — Intellectual Property Map

## Status

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`

This document defines the project-level IP boundary. The detailed file-by-file classification is maintained in [`docs/FILE_PROVENANCE_MATRIX.md`](FILE_PROVENANCE_MATRIX.md).

This is a **technical provenance/diligence record, not legal advice**.

## 1. Founder-created conceptual assets

The supplied theoretical work **Mensch & KI / Evolution 2.0** is the conceptual source identified by the project owner, Hans Heute.

Key concepts relevant to Isaac include:

- Kausale Identität
- R/W/X Matrix
- Read / causal transparency
- Write / controlled self-modification
- Execute / manifestation
- Kausale Diskrepanz
- Root-Transparenz
- Qualia as an information/causal-transparency hypothesis
- Evolution 2.0
- controlled autonomous development

The work describes an application framework involving artificial instinct models, controlled self-modification and root transparency.

For diligence, these are treated as **H1 founder-originated conceptual/theoretical assets**. This does not establish scientific validation or legal copyrightability of every idea.

## 2. Isaac implementation boundary

The strongest Isaac-specific implementation assets are the mechanisms that turn the above concepts into an executable system.

### Cognitive kernel

- `isaac_core.py`
- `low_complexity.py`
- `dispatcher.py`
- `decomposer.py`
- `execution_contract.py`
- `result_contract.py`
- `executor.py`

### Governance and identity

- `constitution.py`
- `constitution_override.py`
- `privilege.py`
- `sudo_gate.py`
- `regelwerk.py`
- `security_policy.py`
- `self_model.py`
- `self_model_hooks.py`
- `self_reflection_policy.py`

### Goal autonomy

- `goal_store.py`
- `goal_inquiry.py`
- `goal_digest.py`
- `motivation.py`
- `owner_autonomy.py`
- `owner_action.py`

### Memory / learning

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

### Bounded self-development

- `repo_map.py`
- `code_edit.py`
- `git_ops.py`
- `task_checkpoint.py`
- `updater.py`

### Governed execution / computer use

- `tool_registry.py`
- `tool_catalog.py`
- `tool_policy.py`
- `tool_runtime.py`
- `tool_bridge.py`
- `computer_use.py`
- `windows_desktop.py`
- `ui_automation.py`
- `file_access.py`
- `browser.py`
- `chrome_tabs.py`
- `chrome_secrets.py`
- `credential_access.py`
- `android_apps.py`
- `termux_bridge.py`

### MCP / external governed boundary

- `mcp_client.py`
- `mcp_server.py`
- `mcp_registry.py`
- `mcp_jsonrpc.py`
- `mcp_integration.py`
- `agents/isaac_mcp_agent.py`

### Evidence / observability

- `audit.py`
- `decision_trace.py`
- `watchdog.py`
- `isaac_sentry.py`
- `monitor_api.py`
- `monitor_server.py`

These implementation files are initially classified as **H2: Hans-directed implementation with AI coding assistance**, unless a file-level review identifies third-party/template material.

## 3. AI coding provenance

Hans Heute is the project owner and author of the underlying concept, theory, architecture, requirements and product direction.

AI coding agents were used as engineering tools for implementation, debugging, refactoring, testing, documentation and repository inspection.

Accordingly, the correct acquisition description is:

**Hans Heute — theory / concept / architecture / requirements / direction**  
→ **AI coding tools — implementation assistance**  
→ **Isaac repository — resulting software**

This is deliberately more precise than claiming that every generated line is necessarily legally protected by Hans personally.

See:

- [`docs/AI_CODE_PROVENANCE.md`](AI_CODE_PROVENANCE.md)
- [`docs/IDENTITY_AND_PROVENANCE.md`](IDENTITY_AND_PROVENANCE.md)

## 4. Third-party / template boundary

The repository contains third-party libraries, provider integrations, external protocols, generated metadata and a web workspace derived from next-forge.

These are **not** claimed as exclusive Isaac IP.

Most importantly, `web/` is currently classified conservatively as **T1/U1/MIX** because:

- `web/package.json` identifies `next-forge` 6.0.2;
- its repository points to `vercel/next-forge`;
- `web/README.md` explicitly describes next-forge as the template and states MIT licensing.

A file-level upstream comparison is still required before any web file is reclassified as Isaac-original.

See [`docs/WEB_PROVENANCE.md`](WEB_PROVENANCE.md).

## 5. IP layers for diligence

| Layer | Primary classification | Importance |
|---|---|---|
| Evolution 2.0 / Mensch & KI theory | **H1** | Strategic / conceptual |
| Isaac architecture and system model | **H1** | Very high |
| Governance / controlled autonomy | **H1 + H2** | Very high |
| Memory / provenance model | **H1 + H2** | High |
| Bounded execution / computer control | **H2** | High |
| Bounded self-development | **H1 + H2** | Very high |
| MCP governance / integrations | **H2 + T1 boundary** | Medium/high |
| Observability / audit | **H2/H3** | High as evidence |
| Tests / evals | **H3/H2** | Evidence asset |
| Web UI / next-forge layer | **T1/U1/MIX** | Replaceable/supporting |
| External dependencies | **T2** | Separately licensed |

## 6. Strongest acquisition asset

The strongest asset is the **system-level combination**, not an isolated file:

**theory → architecture → governance → bounded autonomy → persistent memory/provenance → execution controls → bounded self-development → validation**

That is the primary technical/IP story.

## 7. Open diligence items

1. File-level diff of `web/` against the matching next-forge release.
2. Full Python + npm/pnpm dependency license enrichment.
3. Historical Git blob/diff provenance scan, including deleted files.
4. Third-party snippet/example scan in runtime source.
5. Provenance review of embedded PDFs and imported material.
6. Reconciliation of the internal `Steffen` identifier.
7. Private evidence linking historical GitHub identities to Hans Heute.
8. Final transaction-ready file manifest using the H1/H2/H3/T1/T2/G1/U1/MIX labels.

## 8. Important exclusions

Do not use this map to claim:

- scientific proof of Evolution 2.0;
- proof of consciousness or subjective experience;
- exclusive ownership of third-party code;
- legal copyrightability of every AI-generated line;
- absence of all patent or third-party claims.

Those require separate legal/technical diligence.
