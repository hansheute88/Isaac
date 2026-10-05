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

### 8. Definitive historical vendored-source finding: aiohttp 3.13.3

A dedicated historical-blob comparison found a byte-identical third-party source file:

- Historical Isaac path: `isaac_complete_release_2026-03-27/web_urldispatcher.py`
- Also present at the historical repository root as `web_urldispatcher.py`
- Historical Git blob SHA: `cfa57a310046c78636d1872f6e4c2e27b6a18a76`
- Upstream repository: `aio-libs/aiohttp`
- Upstream tag: `v3.13.3`
- Upstream file: `aiohttp/web_urldispatcher.py`
- Upstream Git blob SHA: `cfa57a310046c78636d1872f6e4c2e27b6a18a76`
- Result: **exact byte-identical blob**
- Size: 44,290 bytes
- The file was introduced by the 2026-04-01 `Initial Isaac GitHub base import` commit and was later moved into `archive/unused/` and ultimately removed from the active tree.

The historical file is therefore **T1 third-party source**, not H2 Isaac-original implementation.

The historical release bundle did not contain a separate aiohttp license/notice file. This is a historical license-compliance diligence item. aiohttp is officially identified as Apache-2 licensed; current PyPI metadata reports Apache-2.0 AND MIT for the package's broader dependency/license metadata. The exact historical source file itself is from aiohttp v3.13.3 and should be treated under aiohttp's applicable license/notice requirements.

This finding does **not** establish that current Isaac runtime code contains the vendored file: the exact file is absent from the current `main` tree.

### 9. Broader historical bundle scan

The 2026-03-27 release bundle contained 58 Python files. Review of their import/marker signatures found no second embedded package source comparable to the exact aiohttp blob. References to aiohttp in `relay.py`, `search.py` and health/monitor code are dependency/API usage, not evidence of vendored aiohttp source.

The root `web_urldispatcher.py` and release-bundle copy are the same Git blob, so they represent one underlying third-party source artifact rather than two independent findings.

### 10. Revised conclusion

The previous statement that no material third-party source had been found in historical Core/release material is superseded.

The corrected conclusion is:

- **One definitive historical third-party source artifact has been identified: aiohttp v3.13.3's `web_urldispatcher.py`.**
- No second comparable vendored runtime source was identified in the reviewed 2026-03-27 release bundle.
- The active/current Isaac tree does not contain this exact vendored file.
- The web/next-forge boundary remains a separate, much larger confirmed third-party/template area.
