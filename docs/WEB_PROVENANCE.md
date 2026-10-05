# Isaac — Web Layer Provenance

## Status

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`

The `web/` workspace is **not currently treated as wholly Isaac-original IP**.

The repository itself identifies the web workspace as `next-forge` 6.0.2, points its repository metadata at `vercel/next-forge`, and its README describes the next-forge Turborepo template. The upstream next-forge repository is publicly identified as an MIT-licensed template: https://github.com/vercel/next-forge

## Current classification

| Path / class | Provenance status | Acquisition treatment |
|---|---|---|
| `web/package.json` | **THIRD-PARTY / TEMPLATE-DERIVED** | Preserve upstream attribution; do not claim as founder-original |
| `web/README.md` | **THIRD-PARTY / TEMPLATE-DERIVED** | Upstream documentation; preserve MIT attribution |
| `web/skills/next-forge/**` | **THIRD-PARTY / TEMPLATE-DERIVED** | Treat as upstream material |
| `web/.autorc` | **THIRD-PARTY / TEMPLATE-DERIVED** | Contains explicit next-forge/Vercel project metadata |
| `web/scripts/**` | **THIRD-PARTY / TEMPLATE-DERIVED until diffed** | Review against upstream before relicensing |
| `web/apps/**` | **TEMPLATE-DERIVED / MODIFIED-STATUS PENDING** | File-level diff required |
| `web/packages/**` | **TEMPLATE-DERIVED / MODIFIED-STATUS PENDING** | File-level diff required |
| `web/**` remaining files | **UNKNOWN / CONSERVATIVE THIRD-PARTY CLASSIFICATION** | Do not include in exclusive-IP claims until reviewed |

## Evidence

The repository's web package metadata contains:

- package name: `next-forge`
- version: `6.0.2`
- upstream repository: `https://github.com/vercel/next-forge.git`

The README contains explicit next-forge branding, upstream documentation references and an MIT license declaration.

Search results also show next-forge-specific implementation artifacts in the workspace, including the updater/initializer scripts, next-forge skills, Vercel metadata, and template-specific UI/content.

## Important distinction

The fact that a file is based on an MIT-licensed template does **not** make the file unusable for a commercial acquisition. It means the provenance and applicable license must be preserved and the file must not be represented as exclusively founder-created code.

The upstream next-forge project is MIT licensed. The actual Isaac dependency graph contains many additional third-party packages whose individual licenses still require enrichment.

## Recommended acquisition treatment

For the cleanest IP boundary, use:

**Isaac cognitive kernel / runtime**  
→ founder-originated concepts + Isaac implementation

**Web layer**  
→ separately classified open-source/template-derived layer

This makes the acquisition claim stronger, not weaker: the buyer can see exactly which part is the proprietary cognitive/control-plane asset and which part is replaceable presentation/infrastructure.

## Next step

Perform a file-level comparison of `web/` against the corresponding upstream next-forge release and classify every file as:

- `[THIRD-PARTY]`
- `[MODIFIED THIRD-PARTY]`
- `[ISAAC-ORIGINAL]`
- `[AI-ASSISTED ISAAC]`
- `[GENERATED]`

Until that comparison is complete, the conservative classification above remains authoritative for diligence.
