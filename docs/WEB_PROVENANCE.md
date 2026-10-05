# Isaac — Web Layer Provenance

## Status

**Classification date:** 2026-10-05  
**Branch:** `acquisition-readiness`

The `web/` workspace is **mixed-provenance and is not wholly Isaac-original IP**.

## 1. Exact upstream baseline resolved

The historical scaffold commit `403536c964ecee90522bfbe5da5b134749ca3d64` identifies the imported material as **next-forge v6**.

The matching upstream version is **next-forge 6.0.2**, represented by upstream commit:

`9aad7123ef8accc79d6ece399f249c46bdb6b138`

This gives us an exact Git-tree baseline instead of a speculative comparison against current upstream.

## 2. Exact Git blob comparison

Current Isaac `web/` tree:

- **423 tracked files**

Upstream next-forge 6.0.2 files sharing paths with Isaac were compared by Git blob SHA.

### Result

| Classification | Count | Meaning |
|---|---:|---|
| **T1** | **380** | exact byte-identical upstream/template content |
| **T1-M** | **40** | same upstream path, but content modified |
| **H2** | **1** | Isaac-only implementation candidate |
| **G1** | **2** | Isaac-only workspace/dependency metadata |
| **U1** | **0** | unresolved at content/hash level |

This is the key finding of the web audit:

> **380 of 423 web files are exact upstream next-forge 6.0.2 content.**

Therefore the majority of the web layer can be confidently treated as template/third-party lineage rather than exclusive Isaac-original code.

## 3. Isaac-only files

Exactly three current web files have no matching upstream path:

### H2 candidate

`web/packages/ai/lib/telemetry.ts`

This was added during Isaac's Sentry/AI-monitoring work. It is currently classified as **H2 candidate** because it appears to be project-specific implementation.

This classification is still a provenance classification, **not a legal conclusion about copyrightability**.

### G1 metadata

- `web/pnpm-lock.yaml`
- `web/pnpm-workspace.yaml`

These are local package-manager/workspace metadata and should not be treated as core proprietary IP.

## 4. Modified upstream files

The 40 T1-M files are descendants of next-forge files with changed content. The full list is recorded in:

`docs/WEB_FILE_PROVENANCE_MANIFEST.md`

Important examples include:

- app environment/configuration files
- app/package manifests
- `package.json`
- AI model integration
- AI keys
- observability integration
- CMS/database/design-system/internationalization/SEO package manifests

A changed SHA does **not** automatically make a file proprietary. These files retain upstream/template provenance and should be treated as **mixed provenance** until section-level review is completed.

## 5. Historical modification evidence

Commit `4bb8318aa502298c7bd62e85b92ff6989640cf95` added/modified the web AI/Sentry integration, including:

- `web/packages/ai/index.ts`
- `web/packages/ai/lib/models.ts`
- `web/packages/ai/lib/telemetry.ts`
- `web/packages/observability/client.ts`
- `web/packages/observability/edge.ts`
- `web/packages/observability/server.ts`
- related package manifests

Dependency update commits subsequently changed package manifests and the pnpm lockfile.

This history is consistent with:

**next-forge scaffold → Isaac-directed modifications/integrations → current mixed web layer**

## 6. Classification rules

| Label | Meaning | Treatment |
|---|---|---|
| **T1** | exact upstream/template match | preserve upstream license/attribution |
| **T1-M** | modified upstream/template | preserve upstream provenance + identify project changes |
| **H2** | Isaac-specific implementation candidate | candidate project asset; retain engineering provenance |
| **G1** | workspace/dependency/generated metadata | supporting infrastructure, not core IP |
| **U1** | unresolved | no exclusive ownership claim |

## 7. Acquisition conclusion

The web layer should **not** be presented as the main proprietary Isaac asset.

The clean technical boundary is:

**Isaac cognitive kernel / Python runtime / governance / memory / autonomy / execution**  
→ **core project asset**

**next-forge-derived web layer + dependencies**  
→ **supporting, separately licensed, partially modified infrastructure**

This is substantially stronger than claiming the whole repository is original.

## 8. Remaining provenance work

The web hash audit and the section-level review of all 40 T1-M files are now complete against the verified 6.0.2 baseline.

The detailed file-by-file delta table is recorded in `docs/WEB_FILE_PROVENANCE_MANIFEST.md`. The 40 changes cluster into:

1. **19 environment-validation changes** adding `SKIP_ENV_VALIDATION` handling.
2. **13 dependency/package-manager changes** covering Next.js, Sentry, sharp, undici, postcss and the Bun→pnpm workspace transition.
3. **5 Sentry/AI observability changes**, which are the largest project-specific runtime modifications in the web layer.
4. **3 Sentry configuration-example changes** in application `.env.example` files.

The single H2 candidate `web/packages/ai/lib/telemetry.ts` remains the clearest Isaac-specific web implementation because it has no upstream counterpart.

Remaining work is narrower:

1. Preserve/verify all third-party notices and licenses.
2. Review the source/provenance of the H2 telemetry file at author/commit level if acquisition precision requires it.
3. Continue the independent dependency-license and historical-secret audits.

**No runtime Isaac code was changed by this audit.**
