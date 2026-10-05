# Isaac — Historical Source Similarity / Provenance Scan

Date: 2026-10-05
Branch: acquisition-readiness
Scope: historical Git commits, deleted release artifacts, historical Python source blobs, and public upstream source comparison.
Purpose: technical provenance diligence. This is not a legal opinion.

## Executive result

The scan found one **definitive exact third-party source artifact** in Isaac's historical Git history:

- Artifact: `web_urldispatcher.py`
- Historical location 1: `web_urldispatcher.py`
- Historical location 2: `isaac_complete_release_2026-03-27/web_urldispatcher.py`
- Isaac Git blob SHA: `cfa57a310046c78636d1872f6e4c2e27b6a18a76`
- Upstream: `aio-libs/aiohttp`
- Upstream tag: `v3.13.3`
- Upstream path: `aiohttp/web_urldispatcher.py`
- Upstream Git blob SHA: `cfa57a310046c78636d1872f6e4c2e27b6a18a76`
- Result: **byte-identical**
- Size: 44,290 bytes

Because the Git blob SHA is identical, this is an exact object-identity match, not a heuristic similarity score.

## Historical lineage

The artifact was introduced in commit:

`4be62cba10ffff28339e12cd0c2ba8f76e134e14`
`Initial Isaac GitHub base import`
2026-04-01

The same artifact was present in the complete release bundle and was later moved/archived and ultimately removed from the active repository. Path history:

1. `isaac_complete_release_2026-03-27/web_urldispatcher.py`
2. historical root `web_urldispatcher.py`
3. moved to `archive/unused/` during repository cleanup
4. no current active-tree occurrence

The current `main` tree does not contain the exact file.

## Upstream comparison

Direct comparison was performed against the official aiohttp source at several tags.

The historical Isaac blob matched progressively:

- aiohttp v3.12.9: high similarity, not identical
- aiohttp v3.13.0: high similarity, not identical
- aiohttp v3.13.1: very high similarity, not identical
- aiohttp v3.13.2: very high similarity, not identical
- **aiohttp v3.13.3: exact blob match**
- aiohttp v3.13.4: similar but not identical

The exact v3.13.3 blob SHA match is the decisive result.

aiohttp's official project metadata identifies the project as Apache-2.0 licensed; current PyPI metadata reports Apache-2.0 AND MIT for the package's broader license metadata. The historical Isaac release bundle did not contain a separate aiohttp license/notice file alongside this source artifact.

## Historical release-bundle scan

The 2026-03-27 complete release bundle contained 58 Python files.

The reviewed Python files were checked for:

- package-internal import structure suggestive of vendored source
- copyright/SPDX/license markers
- obvious framework/package source signatures
- aiohttp, Starlette, FastAPI, Flask, MCP, LangChain, Aider and related markers
- suspicious package-style source layouts

No second embedded runtime source artifact comparable to the exact aiohttp blob was identified in this reviewed bundle.

Normal imports such as:

- `aiohttp` in `relay.py` and `search.py`
- `websockets` in `monitor_server.py`
- `requests` in `tool_runtime.py`
- Flask integration in dashboard/API files

are dependency/API usage, not evidence of vendored package source.

## Historical Core / agent-framework checks

Targeted historical and repository-wide searches found no evidence that Isaac's cognitive kernel is a wholesale import of:

- Aider
- OpenHands
- Cline
- LangChain
- CrewAI
- AutoGPT
- LangGraph

Isaac explicitly documents some external patterns as inspirations, including:

- OpenParallax — Think ≠ Act
- Aider-inspired SEARCH/REPLACE and RepoMap patterns
- Langfuse-like observability terminology

These should remain classified as architectural inspiration unless a separate source-code match is established.

## Current active tree

The exact aiohttp blob is not present in the current active tree.

The current web workspace remains a separate confirmed third-party/template boundary: next-forge-derived material and related generated/provider components.

## Classification

The exact historical aiohttp file is:

**T1 — Third-party source**

It must not be represented as Isaac-original IP.

The historical presence should remain disclosed in acquisition diligence even though the artifact is no longer part of the active runtime tree.

## Limitations

This report is substantially stronger than a keyword-only audit but is not a mathematical proof of originality of every historical line.

GitHub Code Search has documented indexing limitations, including default-branch indexing and file-size/searchability restrictions. Historical deleted blobs therefore cannot be exhaustively compared against every public repository using GitHub Code Search alone.

The strongest available evidence here is:

1. complete Git commit/tree inspection available through the GitHub API;
2. historical blob retrieval;
3. exact Git blob identity against known upstream source;
4. targeted public-code similarity searches;
5. explicit third-party/inspiration markers in the repository.

A commercial-scale source-similarity service or a locally materialized Git object database could extend the scan further, but it is not required to classify the exact aiohttp finding.

## Corrected diligence conclusion

The previous preliminary statement "no material third-party source in historical Core/release material" is superseded.

The technically accurate conclusion is:

> One exact historical third-party source artifact was identified: aiohttp v3.13.3's `web_urldispatcher.py`. It was subsequently archived/removed and is absent from the current active tree. No second comparable vendored runtime source was identified in the reviewed historical release bundle. The active Isaac cognitive/governance/autonomy core remains a strong H2 candidate, subject to the general limitations of source-similarity analysis and the separate third-party/template boundaries already documented.
