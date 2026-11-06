# Isaac 2.0 — A0 Baseline

Branch: isaac-2.0/masterplan
Baseline main commit: cb8de2f16622a90a3fa3b300c69ca1b32962eef1
Baseline observed: 2026-10-05
Runtime test status: not executed by the GitHub connector; repository inspection only.

## A0.1 Existing assets relevant to 2.0

| Capability | Existing evidence | 2.0 action |
|---|---|---|
| Task execution | executor.py | extend, do not replace |
| Decision trace | decision_trace.py | make causal event source |
| Append-only audit | audit.py | remain immutable evidence source |
| Watchdog | watchdog.py | add capability-aware degradation |
| Provider routing | relay.py, watchdog blacklist | connect to trust/quarantine |
| Tool policy | tool_policy.py | integrate with R/W/X |
| Privilege | privilege.py | remain authoritative |
| Security confirmation | security_policy.py | remain authoritative |
| Constitution | constitution.py / override | remain authoritative |
| Memory | memory.py | remain source of truth |
| Task graph/evidence | executor.Task | reuse for causal graph |
| Eval harness | evals/ | add Isaac 2.0 benchmark suite |

## A0.2 Current architecture observation

Isaac already implements a layered architecture: ROT control/governance, BLAU memory/context, GRÜN execution/provider/tool.

The current task object already contains graph-like fields (dependencies, goal_id, actions, evidence, decision, outcome, learned_from) and a DecisionTrace.

Therefore the first 2.0 implementation should be an adapter/normalization layer, not a parallel task graph.

## A0.3 Critical architecture constraint

There must be one authority for each decision domain:

- Privilege → privilege.py
- Security confirmation → security_policy.py
- Constitution → constitution gates
- Tool eligibility → tool_policy.py
- Execution → executor.py
- Audit evidence → audit.py

R/W/X is an additional capability representation and evaluator. It must not silently override the existing authorities.

## A0.4 Main gaps for 2.0

1. No canonical R/W/X capability schema.
2. Existing audit/decision events are not yet normalized into a causal graph schema.
3. Watchdog/provider blacklist is not yet capability-aware.
4. No verified quarantine state machine.
5. No experimentally validated transparency/control index.
6. No standardized fault-injection benchmark for the proposed 2.0 claims.
7. No governance evidence package generated from a complete run.

## A0.5 First implementation target

Capability model → capability decision event → existing privilege/security gates → audit event → DecisionTrace

No provider quarantine or scoring should be implemented until this event path is stable.

## A0.6 Validation requirement

Before A0 is declared complete, run the repository's own validation commands from AGENTS.md. The reported result must be the actual runtime result, not an inferred result from repository contents.