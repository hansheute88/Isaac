# Isaac — SBOM / Dependency Inventory

**Branch:** `acquisition-readiness`  
**Generated:** 2026-10-05  
**Project:** Isaac 5.4.0

## Scope

This is the first acquisition-readiness SBOM inventory generated from the repository's checked-in dependency manifests.

Sources:

- `requirements.txt`
- `requirements-memory-extra.txt`
- `web/package.json`
- `web/pnpm-lock.yaml`

## Inventory result

- npm/pnpm package identities extracted from the lockfile: **2280 unique name/version entries**
- Python direct dependency specifications inventoried: **9**
- CycloneDX components emitted: **2289**

## Important limitation

The inventory is **not yet license-complete**. The CycloneDX components deliberately carry `isaac:license-status = not-enriched` until each dependency's authoritative license metadata is verified.

Likewise, Python transitive dependencies are not fully resolved because the repository does not currently contain a Python lockfile covering the complete runtime dependency graph.

Therefore this file is an **SBOM inventory baseline**, not the final legal sign-off for an acquisition.

## Direct Python manifests

```text
aiohttp >=3.9.0
websockets >=12.0
python-dotenv >=1.0.0
playwright >=1.40.0
chromadb >=0.4.0
Flask >=3.0.0
sentry-sdk >=2.60.0
mem0ai >=0.1.0
cognee >=1.0.0
```

## Web/template finding

The web workspace identifies itself as `next-forge` 6.0.2 and its README describes the Vercel next-forge template. The upstream project is MIT licensed. The Isaac web workspace therefore remains explicitly classified as third-party/template-derived until file-level provenance is completed. See `docs/WEB_PROVENANCE.md`.

## Next diligence pass

1. Enrich every component with authoritative license information.
2. Detect copyleft / source-disclosure obligations.
3. Generate vulnerability findings for exact resolved versions.
4. Resolve Python transitive dependencies with a lockfile or reproducible environment export.
5. Produce a file-level provenance map for `web/`.
6. Verify third-party NOTICE/attribution requirements.
