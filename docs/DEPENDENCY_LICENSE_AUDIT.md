# Isaac — Dependency License Audit

**Date:** 2026-10-05  
**Branch:** `acquisition-readiness`

This is an acquisition-diligence license pass. It is **not legal sign-off**.

## 1. Direct Python dependencies

The repository declares nine direct Python specifications across `requirements.txt` and `requirements-memory-extra.txt`.

| Package | Repository spec | License metadata verified | Initial risk |
|---|---|---|---|
| aiohttp | `>=3.9.0` | **Apache-2.0 AND MIT** | Low; preserve both applicable notices |
| websockets | `>=12.0` | **BSD-3-Clause** | Low |
| python-dotenv | `>=1.0.0` | **BSD-3-Clause** | Low |
| playwright | `>=1.40.0` | **Apache-2.0** | Low; review bundled browser/license notices separately |
| chromadb | `>=0.4.0` | **Apache-2.0** | Low direct; transitive graph still requires review |
| Flask | `>=3.0.0` | **BSD-3-Clause** | Low |
| sentry-sdk | `>=2.60.0` | **MIT** | Low |
| mem0ai | `>=0.1.0` | **Apache-2.0** | Low |
| cognee | `>=1.0.0` | **Apache-2.0** | Low |

Authoritative metadata was checked against PyPI project pages during this pass.

Sources:

- https://pypi.org/project/aiohttp/
- https://pypi.org/project/websockets/
- https://pypi.org/project/python-dotenv/
- https://pypi.org/project/playwright/
- https://pypi.org/project/chromadb/
- https://pypi.org/project/Flask/3.1.3/
- https://pypi.org/project/sentry-sdk/
- https://pypi.org/project/mem0ai/
- https://pypi.org/project/cognee/

## 2. Root web package dependencies

The root `web/package.json` declares:

| Package | Declared version | License metadata | Initial risk |
|---|---:|---|---|
| `@clack/prompts` | `^1.1.0` | **MIT** | Low |
| `commander` | `^14.0.3` | **MIT** | Low |
| `nypm` | `^0.6.5` | **MIT** | Low |

The current lockfile resolves these to:

- `@clack/prompts` 1.7.0
- `commander` 14.0.3
- `nypm` 0.6.8

Sources:

- https://www.npmjs.com/package/@clack/prompts
- https://www.npmjs.com/package/commander
- https://www.npmjs.com/package/nypm

## 3. Important limitation

This pass does **not** establish that all 2,280 npm/pnpm components are license-complete.

The existing SBOM contains:

- 2,280 unique npm/pnpm name/version entries
- 9 direct Python specifications
- 2,289 CycloneDX components

The remaining work is to enrich the exact resolved dependency closure, including transitive Python dependencies and every npm/pnpm package, with authoritative SPDX/license metadata.

## 4. Copyleft / source-disclosure screening

No direct dependency identified in this first pass is known from the verified metadata above to be GPL/AGPL/LGPL/copyleft.

That statement applies **only to the packages listed in this document**. It must not be generalized to the complete transitive dependency graph until the SBOM is fully enriched.

## 5. Special review items

### Playwright

Playwright itself is Apache-2.0, but the runtime downloads browser binaries. The acquisition package should separately document the licensing/provenance of those browser binaries and any bundled third-party components.

### aiohttp

PyPI reports an SPDX-style expression of **Apache-2.0 AND MIT**. Both applicable license obligations/notices should be preserved.

### next-forge

The web template is separately governed by its upstream license/provenance. See:

- `docs/WEB_PROVENANCE.md`
- `docs/WEB_FILE_PROVENANCE_MANIFEST.md`

## 6. Next dependency-diligence steps

1. Enrich every CycloneDX npm/pnpm component with exact resolved-version license metadata.
2. Resolve Python transitive dependencies reproducibly.
3. Detect GPL/AGPL/LGPL/MPL and other reciprocal-license components.
4. Check package-level NOTICE/attribution obligations.
5. Generate a final license/notice bundle for transaction diligence.
6. Run a vulnerability scan against exact resolved versions separately from the license audit.

**Status:** direct-dependency license pass started; full dependency license closure remains pending.
