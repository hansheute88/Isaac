# Isaac — SBOM / Dependency Inventory

**Branch:** `acquisition-readiness`  
**Generated:** 2026-10-05  
**Project:** Isaac 5.4.0

## Scope

This acquisition-readiness SBOM inventory is generated from checked-in dependency manifests.

Sources:

- `requirements.txt`
- `requirements-memory-extra.txt`
- `web/package.json`
- `web/pnpm-lock.yaml`

## Inventory result

- npm/pnpm package identities extracted from the lockfile: **2280 unique name/version entries**
- Python direct dependency specifications inventoried: **9**
- CycloneDX components emitted: **2289**

## License status

The initial direct-dependency license pass is now documented in:

`docs/DEPENDENCY_LICENSE_AUDIT.md`

Verified direct packages in that pass are currently classified as permissive licenses:

- aiohttp — Apache-2.0 AND MIT
- websockets — BSD-3-Clause
- python-dotenv — BSD-3-Clause
- playwright — Apache-2.0
- chromadb — Apache-2.0
- Flask — BSD-3-Clause
- sentry-sdk — MIT
- mem0ai — Apache-2.0
- cognee — Apache-2.0
- root web packages @clack/prompts / commander / nypm — MIT

## Important limitation

The SBOM is **not yet license-complete**.

The CycloneDX components currently use `isaac:license-status = not-enriched` until exact dependency metadata is verified.

Python transitive dependencies are also not fully resolved because the repository does not currently contain a complete Python lockfile for the runtime dependency graph.

Therefore this file remains an **SBOM inventory baseline**, not final legal sign-off.

## Web/template provenance

The web workspace is now audited against the exact next-forge 6.0.2 Git tree.

Current result:

- **423** web files
- **380** exact upstream blob matches
- **40** modified upstream/template files
- **1** Isaac-local implementation candidate
- **2** local dependency/workspace metadata files

See:

- `docs/WEB_PROVENANCE.md`
- `docs/WEB_FILE_PROVENANCE_MANIFEST.md`

## Next diligence pass

1. Enrich all 2,280 npm/pnpm components with authoritative exact-version license metadata.
2. Resolve Python transitive dependencies reproducibly.
3. Detect reciprocal/copy-left licenses.
4. Verify NOTICE/attribution obligations.
5. Produce a final license/notice bundle.
6. Run an exact-version vulnerability scan separately from the license audit.
