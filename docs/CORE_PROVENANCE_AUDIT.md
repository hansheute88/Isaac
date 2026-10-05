# Isaac — Core Provenance Audit

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`  
**Scope:** core Python cognitive/control implementation  
**Purpose:** technical provenance and acquisition diligence; not a legal opinion.

## 1. Identity reconciliation

The project owner has clarified that the GitHub identities/names `Sc0rP` / `sco0rp`, `glinkasteffen075-bit`, `hansheute88`, **Steffen**, and **Hans Heute** refer to the same person.

The Git history is therefore treated as **account-level provenance**, not as evidence of multiple independent project contributors.

Examples from the historical commit metadata:

- Commit `45fe0225fb28965453ce6e55a938d84080495d6f` records author/committer `Sc0rP <glinkasteffen075@gmail.com>`.
- Commit `42bb77c4cc09abdf1c2023f082638990e7ca02d5` records `sco0rp <sco0rp@users.noreply.github.com>`.
- Commit `90f013d11e756bd9cc80a19fd1ba168560a5d23a` records the same `sco0rp` identity.
- Commit `c1067430303a22ea88f98a52cfb8f30018279a13` records `hansheute88 <hansheute88@gmail.com>`.

This establishes different Git identities in the history. The conclusion that they are all the same human is based on the project owner's explicit identity statement and should be backed by private account evidence during formal diligence.

## 2. Strong core implementation milestones

### Governance / constitution

Commit `45fe0225fb28965453ce6e55a938d84080495d6f` (2026-07-07) implemented the Phase 3 governance/self-model slice. The commit modified:

- `executor.py`
- `isaac_core.py`
- `memory.py`
- `privilege.py`
- `tool_runtime.py`
- `values.py`
- `vector_memory.py`
- `audit.py`

The commit message explicitly describes constitution gating before tool execution, task checkpoints, self-model updates, bounded value updates, development-event logging, and confirmation policy for high-risk privilege actions.

**Provenance classification:** H2 — Hans-directed Isaac implementation with AI coding assistance, subject to any file-level third-party findings.

### Goal-directed autonomy

Commit `42bb77c4cc09abdf1c2023f082638990e7ca02d5` (2026-07-15) added `goal_store.py` and kernel goal handlers for persistent owner-directed goals.

Commit `90f013d11e756bd9cc80a19fd1ba168560a5d23a` (2026-07-15) added `motivation.py` and the background autonomy tick, including ranking active owner goals, automatic subgoal creation, analysis-task enqueueing, and a DecisionTrace MOTIVATION phase.

These are strong evidence for the project's goal-directed autonomy implementation lineage.

**Provenance classification:** H2, with third-party/API review still required for individual implementation fragments.

### Epistemic memory / kernel verification

Commit `227fcccbbb236e20e920840758b4190f56862c97` (2026-09-21) added the Prove-the-Kernel framework and modified `memory.py`, `executor.py`, and `learning_engine.py`. It explicitly introduced an Epistemic Memory model, formal TaskGraph/Learning Commit mechanisms, kernel metrics, and a 100-task benchmark.

The GitHub commit metadata records `google-labs-jules[bot]` as the author/committer and `hansheute88` as a co-author in the commit message.

**Important:** this is engineering provenance. It does not make Jules a legal owner or independent project contributor. It records that an external coding agent identity was used as an implementation tool for a Hans-directed project change.

**Provenance classification:** H2/H3 with explicit AI-agent provenance.

### Windows native computer control

Commit `c1067430303a22ea88f98a52cfb8f30018279a13` (2026-10-03) records `hansheute88 <hansheute88@gmail.com>` and adds `windows_desktop.py`, while modifying `computer_use.py` and the Windows installer workflow.

The commit message describes native desktop control helpers, native desktop computer use, user-level setup and runtime validation.

**Provenance classification:** H2.

## 3. What the history does and does not prove

The history provides strong evidence of:

1. continuous project development;
2. project-specific implementation milestones;
3. the evolution of governance, autonomy, memory, execution and computer-use mechanisms;
4. use of AI coding agents as implementation tools;
5. multiple Git identities appearing in the history.

The history alone does **not** prove:

- legal copyright ownership of every individual line;
- that every generated line is copyright-protected;
- absence of third-party snippets;
- absence of patent claims;
- that an AI agent has no contractual rights under every applicable service agreement;
- scientific validity of the underlying Evolution 2.0 theory.

## 4. Acquisition interpretation

For technical diligence, the core should be presented as:

**Hans Heute — theory / concept / architecture / requirements / project direction**  
→ **human + AI coding tools — implementation, testing, debugging and refactoring**  
→ **Isaac core — resulting project-specific software**

The strongest asset is the integrated system-level implementation:

**conceptual framework → cognitive kernel → governance → goal-directed autonomy → provenance-aware memory/learning → bounded execution → computer control → audit/evaluation**

This is a more defensible description than attributing every source line to a human author or claiming AI-generated code as automatically proprietary.

## 5. Remaining core diligence

Still required before a transaction-ready conclusion:

- historical blob/diff scan for deleted or replaced core files;
- third-party snippet/example scan across runtime Python;
- exact dependency/license closure;
- review of embedded research/reference material;
- private evidence package linking all historical Git identities to Hans Heute;
- review of AI-service terms applicable at the dates the coding agents were used.

No runtime code was changed by this audit.
