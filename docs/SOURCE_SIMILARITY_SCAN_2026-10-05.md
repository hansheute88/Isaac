# Historical Source-Similarity & Artifact Provenance Scan — 2026-10-05

## Scope

This report records the next systematic provenance pass after the core/web provenance audits.

Sources inspected:

1. Git history and Git trees of `hansheute88/Isaac`.
2. Historical Isaac source archive `Isaac-main (12).zip` supplied in the working environment.
3. Nested historical archive `.github/instructions/Isaac-main (4).zip` contained inside that ZIP.
4. Public GitHub code search for distinctive Isaac identifiers/fragments.
5. Official/public repositories used as known comparison baselines, especially Aider and OpenParallax.
6. Third-party artifacts and explicit external-source references inside the historical archive.

This is a technical provenance/similarity audit, not a legal opinion.

## Historical archive inventory

The supplied `Isaac-main (12).zip` contains:

- 682 files total.
- 157 Python files.
- 1 nested ZIP: `.github/instructions/Isaac-main (4).zip` (928,939 bytes).
- 1 VS Code extension package: `ms-azuretools.vscode-docker-2.0.0.vsix`.
- No Git metadata.

The nested ZIP contains 188 files, including 75 Python files and the March/April release manifests and implementation notes.

## Release-bundle provenance

Historical March release documentation lists 17 source archives with SHA-256 hashes and sizes, including:

- `26.03.zip`
- `isaac_complete_bundle_v1_v5.zip`
- `isaac_complete_integrated_package_v7.zip`
- `isaac_current_full_backup.zip`
- `isaac_v1_foundation_patch_package.zip`
- `isaac_v2_phase2_patch_package.zip`
- `isaac_v3_phase3_patch_package.zip`
- `isaac_v4_phase4_patch_package.zip`
- `isaac_master_deploy_package_v5.zip`
- `isaac_ultra_deploy_package_v5.zip`
- `isaac_latest_state_orchestrator_openrouter.zip`
- `isaac_dashboard_tools_patch.zip`
- `isaac_hybrid_runtime_bundle.zip`
- `isaac_install_helper.zip`
- `isaac_cumulative_stability_fix.zip`
- `isaac_model_override_fix.zip`
- `isaac_deploy_backup.zip`

The historical `RELEASE_MANIFEST.json` records exact SHA-256 values for these archives.

Important limitation: these ZIPs are not present as ZIP blobs in the current Git tree. The March release notes explicitly describe the archives as historical/original sources, but the current tree contains the extracted runtime rather than the archive bytes. Therefore the manifest proves that the files were referenced and hashed, but does not by itself establish independent possession of the original archive bytes today.

## Initial GitHub import boundary

The Isaac2 repository contains an explicit commit:

`4be62cba10ffff28339e12cd0c2ba8f76e134e14`
`Initial Isaac GitHub base import`

The repository tree at that historical point contains the extracted Isaac runtime but no ZIP blobs. This establishes the GitHub import as a provenance boundary: the Git history begins after the referenced archive-based development process.

The historical Phase 1 notes state that the selected Phase 1 base was:

- `isaac_project_full_20260328_003927.zip`
- plus `isaac_combined_updates_after_project_full_20260330.zip`

and explicitly describe the package as a curated stability package rather than proof that every historical archive is safe to merge wholesale.

## Public source-similarity checks

### Aider

Isaac explicitly documents Aider as an inspiration for three native modules:

- `repo_map.py`
- `code_edit.py`
- `git_ops.py`

The historical archive states:

- “Aider-inspired pattern — not a wholesale import.”
- “Aider-style blocks.”
- “wholesale aider import” is explicitly prohibited.

Direct comparison against Aider's public `editblock_coder.py` and `repomap.py` shows a materially different implementation architecture:

- Isaac does not import the `aider` package.
- Isaac uses its own dataclasses and APIs.
- Isaac adds Constitution/path/owner gates.
- Isaac defaults edit application to dry-run/safe behavior.
- Isaac uses Python stdlib AST for its default RepoMap path rather than Aider's tree-sitter/grep-ast stack.

Conclusion: **documented conceptual/pattern derivation; no evidence of wholesale Aider source import in the inspected Isaac core.**

### OpenParallax

Isaac explicitly records the OpenParallax “Think ≠ Act” concept as an architectural influence. Public OpenParallax documentation confirms that its central design is separation between reasoning and execution with an independent security layer.

No evidence was found in the inspected Isaac Python archive of wholesale Go/Python OpenParallax runtime source being copied into Isaac. Isaac implements its own Python kernel/executor/governance structure.

Conclusion: **architectural influence, not demonstrated source-code copy.**

### Other agent frameworks

Public GitHub searches for distinctive Isaac-specific identifiers such as:

- `IsaacSubgoal`
- `OwnerGoal`
- `DivaModulator`
- `ToolEligibilityDecision`
- `apply_constitution_gate`
- `build_override_context`
- `MCP_TOOL_PRIVILEGES`
- `goal_autonomy_enabled`

returned Isaac repositories or unrelated false positives, not an independent public implementation matching the Isaac core.

The `EpistemicMemoryEntry` identifier has an unrelated public hit in another repository, but the surrounding implementation and semantics are different; the identifier alone is therefore not evidence of copying.

## Third-party artifacts found inside the supplied historical archive

### 1. VS Code Docker extension

`ms-azuretools.vscode-docker-2.0.0.vsix` is an external Microsoft artifact.

Its package metadata identifies:

- publisher: `ms-azuretools`
- repository: `microsoft/vscode-docker`
- version: `2.0.0`
- MIT license.

The VSIX also contains a third-party notice listing incorporated open-source components.

Classification: **T1 third-party artifact**. It must not be represented as Isaac-original IP.

### 2. Letta OpenAPI schema

`openapi_letta.json` is a large OpenAPI 3.1 schema explicitly titled “Letta API”, version 0.16.8.

It contains Letta endpoint and schema definitions and should be treated as **third-party API specification material / generated reference data**, not Isaac-original source code.

Classification: **T1/T2 — third-party API specification/reference artifact.**

### 3. External tool references

`security_toolkit.py` references external tools such as RouterSploit and records the public repository URL:

`https://github.com/threat9/routersploit.git`

This is an integration/reference, not evidence that RouterSploit source was copied into Isaac.

### 4. Remote execution of speedtest-cli

The historical `owner_action.py` contains a network test path that executes:

`curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3`

This is not a source-similarity finding; it is a **supply-chain/runtime provenance finding**. The code executes externally hosted source at runtime rather than vendoring it.

Classification: **external runtime dependency / supply-chain risk**, requiring separate security and dependency review.

## Generated/reference material

`ISAAC_FULL_CODE.txt` is a large consolidated export containing source files, documentation, OpenAPI/reference material and web/template material. It should not be counted as an independent source-code origin because it largely reproduces other files from the same project.

It also explicitly preserves attribution such as:

- Aider-inspired patterns.
- OpenParallax/Langfuse-inspired concepts.
- next-forge material.
- Letta/Mem0 references.
- Contributor Covenant/next-forge material in the web section.

## Similarity conclusion

Current evidence supports the following classification:

| Area | Current conclusion |
|---|---|
| Isaac Python core | No independent public source identified in targeted searches |
| Aider | Pattern/architecture inspiration; no wholesale import found |
| OpenParallax | Architectural inspiration; no wholesale source import found |
| Goal/Constitution/DIVA core | No independent public matching implementation identified |
| Windows computer-use layer | No independent public matching Isaac-specific implementation identified |
| MCP core | Isaac-specific implementation around the MCP protocol; protocol itself is third-party |
| Letta OpenAPI | Third-party reference/schema material |
| VS Code Docker VSIX | Third-party MIT-licensed artifact |
| next-forge web | Confirmed third-party/template boundary; separately audited |
| speedtest-cli | External runtime code execution; supply-chain issue |
| Historical ZIPs | Documented by SHA-256 manifests but not currently present as Git blobs |
| Pre-GitHub authorship/provenance | Not established by Git history alone |

## Residual diligence gap

A true transaction-grade “all historical blobs against all public repositories” result still requires a large-scale source-similarity corpus/search service or a local mirror of the relevant public-code corpus. GitHub code search is useful for distinctive fragments but is not equivalent to a full public-code clone corpus.

Therefore this report deliberately does **not** state that every historical line is unique.

The strongest defensible conclusion is:

> No material evidence of wholesale third-party agent-framework code was identified in the inspected historical Isaac core. Known external influences and third-party artifacts are identifiable and can be separated. The remaining material uncertainty is the provenance of the pre-GitHub archive inputs and exhaustive similarity against the entire public-code universe.

## Recommended next diligence layer

1. Preserve the supplied `Isaac-main (12).zip` as a separately hashed evidence artifact.
2. Preserve the nested `Isaac-main (4).zip` and calculate its SHA-256.
3. Build a file-level provenance manifest for all 157 historical Python files.
4. Compare historical archive files against current Isaac Git blobs by exact SHA/content.
5. Run a dedicated token/AST similarity scan against selected public agent/security repositories.
6. Audit all third-party artifacts and generated API schemas for license/notice obligations.
7. Remove or replace runtime `curl | python3` dependencies before an acquisition package.
8. Keep the pre-GitHub archive provenance explicitly marked as an evidence gap rather than filling it with assumptions.
