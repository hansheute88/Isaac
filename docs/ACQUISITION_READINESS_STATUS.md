# Isaac — Acquisition Readiness Status

**Branch:** `acquisition-readiness`  
**Date:** 2026-10-05

## Completed

- [x] Dedicated `acquisition-readiness` branch created from `main`
- [x] Founder identity / historical GitHub identity clarification documented
- [x] Root copyright notice corrected to the project owner
- [x] AI-assisted development provenance documented
- [x] Initial IP map created
- [x] Initial CycloneDX SBOM inventory created
- [x] Third-party replacement strategy documented
- [x] Web layer identified as next-forge-derived
- [x] Conservative web provenance classification added

## Important identity reconciliation

The acquisition documents identify the owner as Hans Heute, while the current runtime contains the internal owner identifier `Steffen` (for example in `constitution.py` and memory source markers). This may be a project alias, but it must **not** be silently equated with the legal owner in diligence documents. Reconcile the identifier with private ownership evidence before a transaction.

## In progress / not yet legal sign-off

### 1. License enrichment

Current SBOM contains 2,280 unique npm/pnpm name/version entries plus 9 direct Python dependency specifications.

**Status:** inventory complete; authoritative license enrichment incomplete.

Required:
- resolve exact package licenses
- identify copyright holders where required
- identify copyleft / source-disclosure obligations
- retain notices for redistributed third-party code
- resolve Python transitive dependency closure

### 2. Web provenance

**Status:** upstream/template lineage established; file-level diff pending.

Required:
- compare the checked-in web files against the relevant next-forge release
- classify unchanged vs modified files
- identify Isaac-original additions
- preserve or restore required upstream notices

### 3. Historical secrets

**Status:** current-tree pattern scan found no obvious real credentials in the patterns checked.

This is **not** a complete Git-history secret audit.

Required:
- scan historical blobs/diffs
- inspect deleted files and old environment/config artifacts
- rotate any credential ever exposed if a real secret is found
- record remediation without publishing the secret

### 4. Dependency vulnerabilities

**Status:** not yet a complete vulnerability assessment.

Required:
- scan exact resolved versions
- separate runtime vulnerabilities from development-only dependencies
- prioritize remotely exploitable and credential-impacting findings

## Acquisition boundary

The strongest claimed asset is not the third-party dependency set.

The strongest asset is:

**Mensch & KI / Evolution 2.0 theory → Isaac architecture → governance → autonomy → memory/provenance → computer-use controls → validation**

The supplied theoretical work explicitly frames Evolution 2.0 around root transparency, controlled write access, auditability/reversibility and controlled development. This document treats those as the project's conceptual provenance, not as independently validated scientific results.

## Current risk rating

| Area | Status |
|---|---|
| Ownership identity chain | **Documented; private evidence should be retained** |
| Root license scope | **Clarified by documentation; third-party exclusions must be respected** |
| Core Isaac provenance | **Strong project-level claim; file-level AI attribution remains incomplete** |
| Web provenance | **Conservative / pending file-level diff** |
| SBOM inventory | **Complete baseline** |
| License compliance | **Pending enrichment** |
| Historical secret audit | **Pending** |
| Vulnerability audit | **Pending** |

## Rule for this branch

No cognitive-kernel feature expansion belongs on this branch.

This branch is reserved for:
- provenance
- licensing
- SBOM
- security cleanup
- acquisition documentation
- reproducibility / diligence evidence
