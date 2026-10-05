# Isaac — License Enrichment Status
## 2026-10-05

### Inventory

Existing CycloneDX SBOM: 2,289 components.

Current state: inventory complete; license enrichment incomplete.

### Reproducibility split

**Web:** `web/pnpm-lock.yaml` provides exact resolved versions.

**Python:** `requirements.txt` and `requirements-free.txt` use open lower-bound ranges; no complete Python lockfile is present.

### Verified license records

- `@clack/prompts@1.7.0` — MIT.
- `commander@14.0.3` — MIT.
- `nypm@0.6.8` — MIT.
- `next@16.3.4` — MIT.
- `react@19.2.4` — MIT.
- `@sentry/nextjs@10.65.0` — MIT.
- `sharp@0.35.4` — Apache-2.0.
- `aiohttp` — Apache-2.0 AND MIT.

### Diligence limitation

A package-by-package transitive license report cannot honestly be called complete until the exact resolved dependency graph is available for every ecosystem. The current Python manifests do not provide that graph.

The next reproducibility artifact should therefore be a pinned Python lock/constraints file with hashes, followed by full license enrichment from authoritative package metadata.

### Required output

The finished enrichment should contain, for every component:

- ecosystem;
- package name;
- exact version;
- PURL;
- license expression;
- license source URL;
- copyright/notice requirement where applicable;
- direct/transitive relationship;
- runtime/dev/optional scope;
- vulnerability status;
- remediation status.

No component should remain marked `not-enriched` in the acquisition-ready SBOM.
