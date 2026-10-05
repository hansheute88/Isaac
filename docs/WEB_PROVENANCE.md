# Isaac — Web Layer Provenance

## Status

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`

The `web/` workspace is **not treated as wholly Isaac-original IP**.

## Historical provenance

The strongest evidence is Git history.

Commit `403536c964ecee90522bfbe5da5b134749ca3d64` is titled **“Add next-forge SaaS monorepo scaffold in web/”**. It introduced the web workspace as a single scaffold commit with **47,979 additions and 0 deletions**. Its commit message explicitly identifies the material as a **next-forge v6 production Turborepo template**.

Current inventory is **423 tracked files**: 192 under `apps/`, 198 under `packages/`, plus configuration/scripts/skills/metadata.

## Direct upstream evidence

The current repository identifies the web layer as next-forge:

- `web/package.json`: `next-forge` 6.0.2, upstream `vercel/next-forge`
- `web/README.md`: explicitly describes next-forge as the template and states MIT licensing
- `web/.autorc`: explicit Vercel/next-forge metadata

Direct comparisons performed against upstream `main`:

| File | Result | Classification |
|---|---|---|
| `web/package.json` | differs | **T1-M** |
| `web/apps/web/app/[locale]/(home)/page.tsx` | **identical content hash** | **T1** |
| `web/packages/ai/index.ts` | differs | **T1-M** |
| `web/packages/ai/lib/models.ts` | differs | **T1-M** |
| `web/packages/ai/lib/telemetry.ts` | no upstream counterpart at current path | **U1 / local addition pending provenance review** |
| `web/packages/observability/client.ts` | differs | **T1-M** |
| `web/packages/observability/edge.ts` | differs | **T1-M** |
| `web/packages/observability/package.json` | differs | **T1-M** |
| `web/packages/observability/server.ts` | differs | **T1-M** |

A differing file is **not** automatically proprietary. It normally means upstream/template material plus project-specific modifications.

## Post-scaffold history

### AI/Sentry integration

Commit `4bb8318aa502298c7bd62e85b92ff6989640cf95` modified/added web files including:

- `web/packages/ai/index.ts`
- `web/packages/ai/lib/models.ts`
- `web/packages/ai/lib/telemetry.ts`
- `web/packages/observability/client.ts`
- `web/packages/observability/edge.ts`
- `web/packages/observability/server.ts`
- related app/package manifests

These are **mixed-provenance** files unless a section-level review proves otherwise.

### Dependency updates

Dependabot/package-update commits modified multiple package manifests and `web/pnpm-lock.yaml`. These are dependency metadata changes, not evidence that template source became Isaac-original.

### Sentry hardening

Commit `d0f38a96dd95dd382f1a363e05dec245d812e647` modified Sentry integration and environment examples.

## Classification scheme

| Label | Meaning |
|---|---|
| **T1** | confirmed unmodified third-party/template |
| **T1-M** | modified third-party/template; upstream provenance remains |
| **H2** | Isaac-specific implementation; verify no copied third-party material |
| **G1** | generated/dependency/build metadata |
| **U1** | unresolved; no exclusive-IP claim yet |

## Current conservative boundary

**T1:** files proven identical to upstream, next-forge README/metadata, upstream skills/reference material, and other confirmed matches.

**T1-M:** files modified after the scaffold, including the identified AI/Sentry integration files and affected package manifests.

**G1:** `web/pnpm-lock.yaml` and generated/package-manager metadata.

**U1:** all remaining files not yet individually compared against the matching upstream release.

## Acquisition conclusion

The web layer should **not** be presented as the core proprietary Isaac asset.

The clean boundary is:

**Isaac cognitive kernel / Python runtime / governance / memory / autonomy / execution**  
→ **core project asset**

**next-forge-derived web layer + dependencies**  
→ **supporting, separately licensed, partially modified infrastructure**

This is more defensible than claiming the entire repository as original.

## Remaining work

1. Resolve the exact upstream next-forge release corresponding to the 2026-07-12 scaffold.
2. Compare all 423 current web files against that release.
3. Produce a final per-file T1/T1-M/H2/G1/U1 manifest.
4. For each T1-M file, record the Isaac-specific modifications.
5. Preserve all applicable third-party notices/licenses.

**No runtime code is changed by this provenance review.**
