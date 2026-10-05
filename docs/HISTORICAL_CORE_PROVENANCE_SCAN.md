# Isaac — Historical Core Provenance / Third-Party Scan

Date: 2026-10-05
Branch: acquisition-readiness
Scope: repository search + selected historical commit/file inspection.
Status: preliminary but materially useful; not a legal opinion and not a cryptographic/exhaustive similarity scan.

## Findings

### 1. Explicitly prohibited wholesale imports are not evidenced
Repository searches for Aider/OpenHands/Cline/LangChain/CrewAI/AutoGPT did not reveal wholesale runtime imports of those frameworks.
Instead, Isaac explicitly documents native implementations: repo_map.py is Aider-inspired, code_edit.py is Aider-inspired SEARCH/REPLACE, and git_ops.py is Aider-inspired commit hygiene.
Assessment: no evidence found of a wholesale Aider/OpenHands/Cline/LangGraph/CrewAI/AutoGPT runtime import.

### 2. Open-source patterns are explicitly acknowledged
The repository contains references to external projects as architectural inspiration, including OpenParallax for Think ≠ Act, Langfuse-like observability terminology, and Aider-inspired repo mapping/code editing/Git hygiene.
These are documented as patterns/inspiration, not source-code imports.

### 3. Web tree contains confirmed third-party/template material
The existing web audit established that the web workspace is next-forge-derived. It also contains explicit next-forge attribution and generated BaseHub/GenQL material.
Examples: web/.github/CODE_OF_CONDUCT.md contains Contributor Covenant attribution; web/packages/cms/basehub-types.d.ts identifies generated BaseHub SDK types and GenQL credit; web metadata/scripts identify next-forge/Vercel lineage.
Assessment: preserve the web third-party boundary.

### 4. MCP configuration contains a third-party server reference
mcp_config.json.example and tests reference @modelcontextprotocol/server-fetch. This is a configuration/dependency reference, not evidence that the server implementation was copied into Isaac.
Assessment: T2/configuration boundary.

### 5. Core architecture document requires caution
docs/PHASE1_ARCHITECTURE_FOUNDATION.md uses InputPacket, BluePacket and GreenTask terminology and describes the Rot/Blau/Grün architecture. The current scan does not establish an external source.
Assessment: H1/H3 candidate; formal provenance should be supported by the owner's original project notes if used in a transaction package.

### 6. modulator.py / DIVA
modulator.py implements uncertainty, caution and curiosity modulators, decay, provenance resolution and audit integration. Git history shows a Jules coding-agent implementation with Hans Heute recorded as co-author. No external source was established by the repository search performed here.
Assessment: H2/H3 with explicit AI-agent provenance.

### 7. remote_smoke.py
remote_smoke.py contains project-specific Render keep-alive and smoke-test logic. No external source was established by the targeted search.
Assessment: H2/H3 candidate.

## Historical milestone evidence
The following commits were inspected at commit metadata/file-list level: 45fe0225... constitution/checkpoints/self-model; 42bb77c4... goal store; 90f013d1... motivation engine/background autonomy; 227fccc... Prove the Kernel/epistemic memory/benchmark; 794793f0... DIVA runtime modulator; c1067430... Windows native user-level computer control.

## Important limitation
GitHub repository search is not a substitute for a full source-code similarity scanner. This audit has not proven that every runtime line is independently written and has not exhaustively compared every historical blob against every public repository.

Transaction-grade follow-up: full Git object/blob inventory including deleted files; source similarity/fingerprint scan against relevant upstream repositories; vendored/generated directory scan; package-license closure; historical secret scan; review of external research documents and copied examples.

## Current conclusion
No material evidence of wholesale third-party agent-framework code in the Isaac core was found in this pass.
The strongest confirmed third-party boundary remains the web/next-forge layer plus dependencies and generated/provider material.
The core cognitive/governance/autonomy implementation remains a strong H2 candidate: Hans-directed implementation with AI coding assistance, subject to exhaustive checks.