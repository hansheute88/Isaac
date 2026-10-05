# Isaac — IP & Third-Party Provenance

## Purpose

This document separates Isaac's founder-controlled intellectual work from third-party software, external services, templates, and AI-assisted implementation.

## 1. Founder-created architecture

The founder states that the Isaac architecture and its underlying conceptual direction originate from his own theoretical work on **Mensch & KI / Evolution 2.0**, including the concepts of:

- Kausale Identität
- R/W/X access model (Read / Write / Execute)
- Root-Transparenz / causal traceability
- controlled self-modification
- bounded autonomy
- persistent memory and learning
- owner-centric governance
- causal auditability
- the transition described as Evolution 2.0

The supplied theoretical work explicitly presents human and artificial intelligence as instances of a common causal functional principle and frames differences in terms of access rights to system state/code. It also proposes controlled self-modification, root transparency and Evolution 2.0 as an application framework.

The theoretical work is the conceptual source; the Isaac repository is the software implementation and experimental engineering embodiment of selected ideas.

## 2. Isaac-specific implementation

The following are treated as Isaac-specific implementation assets and must be distinguished from external libraries:

- cognitive-kernel orchestration
- Classification → Retrieval → Strategy → Task → Execution → Evaluation → Memory pipeline
- Constitution / governance boundaries
- Goal Store / Subgoals / Motivation
- decision traces and audit mechanisms
- typed memory model and provenance
- bounded computer-use layer
- MCP governance and boundary enforcement
- Windows desktop integration
- coding subsystem and bounded Git operations
- Isaac-specific tests, evaluation harnesses and runtime policies
- Isaac documentation and architecture specifications

## 3. AI-assisted implementation

Coding agents have been used as implementation, testing, debugging and refactoring tools. The project owner controlled requirements, architecture, scope, acceptance criteria and validation.

Relevant agent/tool history includes Jules, Copilot, Codex and other coding assistants used during development. Exact per-file attribution should be reconstructed from Git history where required.

No API keys, credentials, private prompts or other secrets belong in this document.

## 4. Third-party open-source components

The repository contains third-party dependencies and a web application derived from / based on the public next-forge template ecosystem.

Important finding:

- `web/package.json` identifies the package as `next-forge` 6.0.2.
- `web/README.md` identifies the project as the next-forge Turborepo template and links to the Vercel next-forge repository.
- This web layer must therefore be treated as third-party/template-derived until a file-level provenance review marks individual files as Isaac-original or materially modified.

## 5. Modified vs. unmodified third-party code

Status at acquisition-readiness branch creation:

- Third-party dependencies: present.
- next-forge-derived web layer: present.
- Complete file-level modified/unmodified classification: **pending**.
- Complete license attribution: **pending SBOM/license enrichment**.

Do not describe the entire repository as wholly original proprietary code.

## 6. External services vs. software IP

External APIs/services (LLM providers, GitHub, Sentry, hosted browser/agent services, etc.) are capabilities Isaac can call. They are not automatically Isaac IP.

Isaac's integration code, governance decisions, adapters and orchestration are separate from the provider's proprietary service.

## 7. Provenance rule

For acquisition diligence, every material component should be classed as one of:

1. Founder-originated concept
2. Isaac-specific implementation
3. AI-assisted implementation under founder direction
4. Third-party open-source code
5. Third-party modified code
6. External service/API integration
7. Generated/build artifact

## 8. Acquisition statement

All GitHub identities used in the Isaac history (including `hansheute88` and `glinkasteffen075-bit` / Sc0rP) are controlled by the same project owner. The account changes were made for trial/subscription purposes and do not represent independent contributors.

This statement should be supported by private account records if a buyer requests identity/provenance evidence.

## 9. Outstanding diligence

- Complete file-level provenance map for the repository, with the web layer tracked separately in `docs/WEB_PROVENANCE.md`.
- Complete license/SBOM enrichment.
- Historical secret scan.
- Dependency vulnerability scan.
- Verify third-party notices and attribution requirements.
- Verify all web/template licenses and notices; the current conservative classification is documented in `docs/WEB_PROVENANCE.md`.
