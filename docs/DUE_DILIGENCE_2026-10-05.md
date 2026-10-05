# Isaac — Technical Due Diligence
## 2026-10-05

## Scope

This document records the first executable due-diligence pass covering:

1. license/SBOM enrichment;
2. historical secret exposure;
3. dependency vulnerability assessment;
4. supply-chain controls.

This is a technical diligence record, not a legal opinion.

## 1. License / SBOM status

### Confirmed inventory

The existing CycloneDX SBOM contains 2,289 components (2,280 unique npm/pnpm name-version entries plus direct Python specifications). The SBOM is currently marked `license-enrichment=pending`.

The web tree has an authoritative lockfile: `web/pnpm-lock.yaml`.

The Python runtime does **not** currently have a complete lockfile. `requirements.txt` uses open lower-bound ranges such as:

- `aiohttp>=3.9.0`
- `websockets>=12.0`
- `python-dotenv>=1.0.0`
- `playwright>=1.40.0`
- `chromadb>=0.4.0`
- `Flask>=3.0.0`
- `sentry-sdk>=2.60.0`

This means an exact, reproducible Python license/vulnerability state cannot yet be asserted from the repository alone.

### Verified license samples

| Component | Version | License evidence |
|---|---:|---|
| `@clack/prompts` | 1.7.0 resolved | MIT |
| `commander` | 14.0.3 | MIT |
| `nypm` | 0.6.8 | MIT |
| `next` | 16.3.4 | MIT |
| `react` | 19.2.4 | MIT |
| `@sentry/nextjs` | 10.65.0 | MIT |
| `sharp` | 0.35.4 | Apache-2.0 |
| `aiohttp` | unpinned range | Apache-2.0 AND MIT |

These samples are authoritative spot checks; they do **not** constitute complete transitive license enrichment.

## 2. Historical secret scan

### Current-tree scan

Targeted current-tree searches found no literal private-key blocks, AWS access-key patterns, OpenAI `sk-proj-` patterns, Slack `xoxb-` patterns, or other obvious high-confidence credential values in the checked patterns.

The repository intentionally contains secret *names*, prefixes and environment placeholders. These are not themselves credentials.

### Historical evidence

A security hardening commit exists:

`765aa249ce121cbc9f326c05587cfc3157a0476a`

Its commit message explicitly says the `.gitignore` was hardened to prevent future secret leaks, especially `ISAAC_ACTIVE_KEYS*`. The resulting ignore rules explicitly describe these as "known leaks from history".

This is a material diligence finding: the repository history should be treated as having had **historical secret-bearing artifacts or suspected secret-bearing artifacts**, even though this audit did not recover or publish a secret value.

The repository also contains a secrets-bootstrap architecture that deliberately loads credentials from local/ignored stores rather than Git.

### Status

**No live secret value was established by the current targeted scan.**

**Historical secret exposure cannot be marked cleared yet.**

For transaction diligence, any credential ever committed should be considered compromised unless its provider-side status proves it was non-secret/test data or it has been revoked/rotated.

## 3. Vulnerability scan

### Confirmed dependency-range risks

#### AIOHTTP

Isaac declares `aiohttp>=3.9.0` without an upper bound or lockfile.

Multiple 2026 advisories affect older aiohttp releases. Current upstream advisories include:

- CVE-2026-54273 through CVE-2026-54279 affecting releases before 3.14.1/3.14.0 depending on the issue;
- CVE-2026-50269 affecting releases before 3.14.0;
- CVE-2026-34993 affecting releases before 3.14.0;
- CVE-2026-34525 and CVE-2026-34520 affecting releases before 3.13.4;
- CVE-2026-69243 affecting releases <=3.14.1.

Therefore the current `>=3.9.0` declaration is **not an acceptable acquisition-grade security specification** by itself.

The exact installed version must be locked and assessed.

#### Flask

Isaac declares `Flask>=3.0.0`.

CVE-2026-27205 affects Flask versions below 3.1.3. Therefore the current lower bound does not establish a patched runtime.

The exact installed version must be locked and assessed.

#### Next.js

The web lockfile resolves `next@16.3.4`.

A critical Windows-hosted RCE advisory affects Next.js `>=16.0 <16.3.3`; therefore 16.3.4 is above that particular fixed boundary.

However, the Next.js advisory feed contains multiple 2026 advisories, so the lockfile must be continuously checked rather than treating one fixed boundary as a blanket security clearance.

#### React Server Components

The repository resolves React 19.2.4. A 2026 advisory affected `react-server-dom-*` 19.2.4 and was fixed at 19.2.5. Whether the vulnerable server component package is actually present and reachable in Isaac's resolved dependency graph must be established from the lockfile/dependency graph before declaring impact.

#### sharp

The repository resolves `sharp@0.35.4`.

A 2026 libheif vulnerability affected versions before 0.35.4 and was fixed at 0.35.4. The locked version is therefore at the published fixed boundary for that advisory.

## 4. Supply-chain controls

GitHub documents that the dependency graph can expose package versions, licenses and known vulnerabilities, and that Dependabot alerts can identify vulnerable dependencies. GitHub also documents historical secret scanning across repository history.

Isaac currently has no committed `.github/dependabot.yml`.

### Remediation added by this diligence phase

A Dependabot configuration should be added for:

- npm/pnpm;
- pip;
- GitHub Actions.

This provides continuous dependency-update/security monitoring once the branch is integrated.

## 5. Acquisition risk classification

| Area | Finding | Risk |
|---|---|---|
| Python dependency reproducibility | No complete lockfile | **High** |
| AIOHTTP lower bound | Permits known vulnerable releases | **High** |
| Flask lower bound | Permits known vulnerable releases | **Medium/High** |
| Web lockfile | Exact resolved versions available | **Good** |
| Next.js | Current locked version above one critical fixed boundary | **Needs continuous advisory scan** |
| React/RSC | 19.2.4 requires graph-level reachability check | **Medium** |
| sharp | 0.35.4 at fixed boundary for identified libheif issue | **Good for that advisory** |
| Current-tree secrets | No high-confidence literal secret found in targeted scan | **Uncleared history** |
| Historical secret evidence | `ISAAC_ACTIVE_KEYS*` explicitly referenced as known historical leak class | **High diligence priority** |
| License enrichment | Inventory exists, full transitive attribution incomplete | **High** |

## 6. Required next remediation

1. Produce a fully locked Python environment with hashes.
2. Resolve every SBOM component to an authoritative license identifier and source.
3. Run a full historical secret scan with Git object traversal and provider-pattern detection.
4. Obtain the repository's authoritative Dependabot/secret-scanning alert state.
5. Generate a resolved-version vulnerability report for both pip and pnpm.
6. Review all high/critical findings before any acquisition representation of the software as security-ready.
7. Preserve this report and the raw machine-readable audit outputs as diligence evidence.

## Conclusion

The due-diligence pass has already uncovered **real acquisition-grade issues**, not merely documentation gaps:

- Python dependencies are not reproducibly locked.
- The current Python version ranges permit known vulnerable releases.
- Git history explicitly references a class of known historical key artifacts.
- The web stack is substantially better controlled because it has a lockfile, but it still requires advisory-level checking.

No secret value is reproduced in this document.
