# Isaac — Deep Technical Source Similarity Audit
## 2026-10-05

### Scope

This audit is the final technical source-similarity pass for the acquisition-readiness branch. It complements the historical 157-Python-file screening, the exact historical aiohttp finding, the web/next-forge provenance audit, and the dependency/license audit.

The goal is **not** to prove legal authorship. The goal is to distinguish:

- exact third-party source;
- substantial source-level similarity;
- documented architectural inspiration;
- ordinary API/protocol usage;
- Isaac-specific implementation.

### Method

1. Historical Isaac Python source set: 157 files in the supplied `Isaac-main (12).zip`.
2. Targeted source-level comparisons against public upstream projects that are materially relevant to the identified provenance boundaries:
   - `aio-libs/aiohttp`
   - `Aider-AI/aider`
   - `modelcontextprotocol/python-sdk`
   - `openparallax/openparallax`
   - Letta / Mem0 were additionally searched for Isaac-specific class and module identifiers.
3. For selected current Isaac files, a lightweight lexical/token Dice similarity was computed against directly relevant upstream files. This is a **screening metric**, not a plagiarism detector and not an AST equivalence proof.
4. GitHub repository searches were used for distinctive Isaac identifiers and architecture terms.
5. Results were classified conservatively.

### Results

| Isaac area | Comparison | Result | Classification |
|---|---|---:|---|
| `web_urldispatcher.py` (historical) | aiohttp v3.13.3 `aiohttp/web_urldispatcher.py` | **100% byte-identical** | **T1 exact third-party** |
| `code_edit.py` | Aider `aider/coders/search_replace.py` | 48.35% lexical token Dice | H2, Aider-inspired; no exact-source finding |
| `repo_map.py` | Aider `aider/repomap.py` | 58.91% lexical token Dice | H2, Aider-inspired; no exact-source finding |
| `git_ops.py` | Aider `aider/commands.py` | 37.46% lexical token Dice | H2, Aider-inspired; no exact-source finding |
| `mcp_jsonrpc.py` | MCP Python SDK `mcp_types/jsonrpc.py` | 28.01% lexical token Dice | H2 protocol implementation; no exact-source finding |
| Isaac goal/autonomy identifiers | Letta | no matching Isaac-specific identifiers found | H2 candidate |
| Isaac motivation/learning identifiers | Mem0 | no matching Isaac-specific identifiers found | H2 candidate |
| Isaac architecture identifiers | OpenParallax | no matching `InputPacket`, `BluePacket`, `GreenTask`, `TaskGraph`, `MemoryPort`, `ExecutionContract` matches found | H1/H2; conceptual comparison only |

### Exact third-party source finding

The historical file:

`web_urldispatcher.py`

was previously verified byte-for-byte identical to:

`aio-libs/aiohttp` v3.13.3, `aiohttp/web_urldispatcher.py`.

Git blob:

`cfa57a310046c78636d1872f6e4c2e27b6a18a76`

Size:

44,290 bytes.

The file entered Isaac history in the initial GitHub base import and was subsequently moved to `archive/unused/` and removed from the active tree. It is therefore recorded as third-party historical material and is **not treated as Isaac-original IP**.

### Aider comparison

Isaac's coding subsystem explicitly describes its implementation as Aider-inspired rather than a wholesale import.

The measured lexical similarities are consistent with that statement:

- `code_edit.py` ↔ Aider search/replace implementation: 48.35%.
- `repo_map.py` ↔ Aider repo map implementation: 58.91%.
- `git_ops.py` ↔ Aider command implementation: 37.46%.

These percentages are not evidence that the Isaac files are copied. They reflect shared programming vocabulary, algorithms, and domain concepts. The repository's own comments already disclose the Aider inspiration. No exact third-party source match was found in the targeted search.

### MCP comparison

Isaac's `mcp_jsonrpc.py` was compared with the official MCP Python SDK JSON-RPC type module.

The token Dice score was 28.01%. The implementation shares protocol-level concepts and names because both implement the MCP/JSON-RPC specification, but no exact-source match was established.

This should therefore be described as:

> Isaac-specific implementation of a third-party protocol, not proprietary ownership of the MCP protocol itself.

### OpenParallax comparison

OpenParallax is relevant as an architectural comparison because it publicly documents separation between reasoning and execution and a security pipeline between them. The targeted repository search did not find Isaac-specific identifiers such as:

- `InputPacket`
- `BluePacket`
- `GreenTask`
- `TaskGraph`
- `MemoryPort`
- `ExecutionContract`
- `constitution_override`

The comparison therefore supports **architectural differentiation**, not source-copy claims.

OpenParallax's own public documentation describes its architecture as a multi-process thinking/acting separation with an independent security pipeline. This is materially related to Isaac's governance/execution concerns, but similarity of architectural problem space is not source-level copying.

### Letta / Mem0 comparison

Targeted searches for Isaac-specific identifiers including `OwnerGoal`, `MotivationDecision`, `DecisionTrace`, `EpistemicMemory`, `GoalStore`, `DIVA`, `owner_confirmed`, and `motivation.py` did not produce matching results in the searched upstream repositories.

Isaac's `external_memory/letta_adapter.py` and `external_memory/mem0_adapter.py` should therefore be treated as **integration/adapter code around third-party services**, while the third-party service itself remains external IP/dependency territory.

### Interpretation

The technical provenance picture is now:

1. **Confirmed third-party source exists historically:** one exact aiohttp file.
2. **Confirmed third-party/template web boundary exists:** next-forge scaffold and modified descendants.
3. **Coding subsystem openly acknowledges inspiration:** Aider-inspired patterns, with no wholesale Aider source match found in the targeted audit.
4. **MCP code is protocol implementation:** no exact SDK source match established.
5. **OpenParallax is an architectural comparison, not a detected source dependency.**
6. **External-memory modules are adapters, not vendored Letta/Mem0 source.**
7. **Core Isaac governance, identity, goals, motivation, memory, evaluation, computer-use, and orchestration modules remain H2/H3 provenance candidates based on the repository history and targeted similarity results.**

### Important limitations

This is a high-confidence **technical screening audit**, not a mathematical proof of source originality.

It does not establish:

- legal authorship or copyright ownership;
- absence of every possible third-party snippet on the public internet;
- patent freedom-to-operate;
- license compliance for every transitive dependency;
- scientific validity of Isaac's conceptual claims.

A complete global source-similarity proof would require a comprehensive public-code corpus and historical versions of every potentially relevant dependency, which is outside the capabilities of this audit.

### Acquisition-readiness conclusion

No new exact third-party source was identified in the targeted core-code similarity pass beyond the already documented historical aiohttp artifact.

The correct acquisition representation is therefore:

**Hans Heute — concept/theory/architecture/product direction and owner requirements → human-directed engineering with AI coding-agent assistance → Isaac implementation**, with explicit third-party/template/dependency boundaries documented separately.

The historical aiohttp file and the next-forge-derived web tree must remain explicitly classified as third-party/template-derived material rather than Isaac-original IP.

This report is a provenance record, not a legal opinion.
