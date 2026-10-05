# Isaac — IP and Third-Party Boundary

## Owner

**Hans Heute is the owner of the Isaac project and the author of its underlying conceptual work.**

The project-level intellectual contribution includes the *Mensch & KI / Evolution 2.0* theory, the Isaac concept, architecture, governance model, autonomy model, memory/provenance model, security requirements, computer-use requirements and implementation direction.

## AI-assisted implementation

Coding agents were used as engineering tools. They assisted with implementation, testing, debugging, refactoring and documentation.

The project should therefore distinguish:

1. **Hans Heute's original conceptual and architectural contribution**
2. **Hans-directed AI-assisted implementation**
3. **third-party open-source/template material**
4. **external services/APIs**

AI coding assistance does not transfer project ownership to the coding tool or provider.

## Third-party material

Third-party dependencies and templates are not claimed as original Isaac IP.

The web workspace currently contains explicit next-forge/template lineage and is conservatively classified in `docs/WEB_PROVENANCE.md`.

## Acquisition rule

The strongest proprietary claim is the combination:

**Hans Heute's theory and system concept → Isaac architecture → governance → bounded autonomy → persistent memory/provenance → execution controls → validation**

The dependency set and template-derived web layer are supporting/replaceable components, not the core ownership claim.

## Required diligence

- preserve applicable third-party licenses and notices
- complete file-level web provenance
- complete dependency license enrichment
- complete historical secret review
- retain private evidence of ownership/control of all historical GitHub identities
- retain development records showing Hans-directed requirements and decisions
- do not represent third-party/template code as founder-original

See `docs/IDENTITY_AND_PROVENANCE.md`, `docs/AI_CODE_PROVENANCE.md`, and `docs/WEB_PROVENANCE.md`.


## Historical vendored-source finding

The historical 2026-03-27 release bundle contained a byte-identical copy of `aiohttp/web_urldispatcher.py` from aiohttp v3.13.3 (Git blob `cfa57a310046c78636d1872f6e4c2e27b6a18a76`). The same blob also appeared at the historical Isaac repository root.

This artifact is classified **T1 third-party source**, not Isaac-original IP. It was subsequently archived and removed and is not present in the current active tree. The transaction package should disclose this historical artifact and its applicable aiohttp license/notice requirements separately from the Isaac H2 core.

The broader current `web/` next-forge/template boundary remains independently classified as third-party/template-derived.
