# ISAAC 2.0 — Masterplan

**Status:** ACTIVE — Architecture & Implementation Program  
**Branch:** `isaac-2.0/masterplan`  
**Base:** `main`  
**Purpose:** Transform Isaac's existing cognitive kernel into a measurable Agent Control, Trust, Audit and Recovery Runtime without a destructive rewrite.

---

## 1. Strategic Target

Isaac 2.0 is not marketed as a consciousness claim.

The product target is:

> **Agent Control & Trust Infrastructure — a runtime that can observe, authorize, constrain, explain and recover autonomous AI actions.**

The existing philosophical R/W/X model becomes a technical capability model.

The four strategic pillars are:

1. **R/W/X Capability Control**
2. **Causal Decision Memory**
3. **Cybernetic Guardrails / Dynamic Quarantine**
4. **Measurable Transparency, Stability and Recovery Benchmarks**

A fifth product layer exposes these capabilities for governance and compliance evidence.

---

## 2. Current Repository Baseline

The current repository already contains substantial relevant infrastructure:

### Existing control/governance
- `privilege.py`
- `security_policy.py`
- `constitution.py`
- `constitution_override.py`
- `sudo_gate.py`
- `tool_policy.py`

### Existing execution
- `executor.py`
- `tool_runtime.py`
- `relay.py`
- MCP infrastructure
- browser/computer-use integrations

### Existing memory
- `memory.py`
- `procedure_memory.py`
- `vector_memory.py` (optional)
- external memory adapters
- goals and learning modules

### Existing observability
- `audit.py`
- `decision_trace.py`
- `watchdog.py`
- `monitor_server.py`
- Sentry/telemetry components

### Existing task graph/evidence fields
`executor.Task` already contains:
- dependencies
- goal/subgoal IDs
- required capabilities
- risk level
- actions
- evidence
- decision
- outcome
- learned_from
- decision_trace

This means the 2.0 architecture should **compose and formalize existing primitives**, not duplicate them.

---

# 3. Target Architecture

```
User / Application
       |
       v
Isaac Runtime
       |
       +--> Intent / Context / Goal
       |
       +--> Policy & R/W/X Capability Engine
       |
       +--> Task / Execution Engine
       |        |
       |        +--> Provider
       |        +--> Tool
       |        +--> Filesystem / Network / OS
       |
       +--> Decision Trace
       |
       +--> Causal Memory / Decision Graph
       |
       +--> Watchdog / Trust / Quarantine
       |
       +--> Verification / Recovery
       |
       +--> Metrics / Benchmark
       |
       +--> Audit / Governance Evidence
```

### Design rule

R/W/X is a **capability layer**, not a second privilege system.

Existing privilege, constitution and confirmation systems remain authoritative. R/W/X must integrate through adapters and policy evaluation rather than bypassing them.

---

# 4. R/W/X Capability Model

## 4.1 Formal capability

Every protected resource receives a capability state:

```json
{
  "resource": "filesystem:/workspace",
  "read": true,
  "write": false,
  "execute": false
}
```

The initial implementation must support:

- resource identity
- principal/agent identity
- R permission
- W permission
- X permission
- policy source
- decision reason
- timestamp
- expiration/version

## 4.2 Resource classes

Initial resource classes:

- filesystem
- process/system command
- network
- provider
- tool
- memory
- configuration
- external service

## 4.3 Planned modules

```
isaac_capabilities/
  model.py
  policy.py
  evaluator.py
  registry.py
  transitions.py
```

Do not create these modules until the interfaces have been validated against existing privilege/security code.

---

# 5. Causal Decision Memory

The existing audit log remains append-only.

The new layer interprets events as a causal graph.

## Node types

- Intent
- Context
- Plan
- Assumption
- Observation
- ToolCall
- ProviderResponse
- PolicyDecision
- Action
- Result
- Error
- Intervention
- Recovery
- Verification

## Edge types

- derived_from
- depends_on
- caused_by
- triggered
- observed
- authorized_by
- blocked_by
- corrected_by
- verified_by

## Principle

The causal graph is derived from immutable events. It is not a replacement for the audit log.

This preserves a clean separation:

```
Audit Log = immutable evidence
Causal Graph = interpretable structure derived from evidence
```

---

# 6. Root-Cause Tracing

For every recoverable failure, Isaac should attempt:

```
failure
  -> relevant event window
  -> causal predecessors
  -> violated assumption/policy/resource
  -> root-cause candidate
  -> confidence
  -> corrective action
  -> verification
```

The system must distinguish:

- observed fact
- inferred cause
- hypothesis
- verified root cause

No inferred cause may be presented as proven without verification.

---

# 7. Cybernetic Guardrail

The current watchdog already detects hangs, restarts tasks and can switch providers.

Isaac 2.0 extends this behavior with capability-aware degradation.

Example state:

```
NORMAL
R=1 W=1 X=1

SUSPICIOUS
R=1 W=0 X=0

QUARANTINED
R=1 W=0 X=0 + restricted network/tool access

RECOVERED
capabilities restored only after verification
```

## Important invariant

A provider/tool can remain readable/observable for diagnosis while its ability to mutate or execute is restricted.

This is the technical implementation of dynamic quarantine.

---

# 8. Provider Trust Model

Each provider receives an operational trust state derived from observed evidence.

Candidate signals:

- successful task rate
- verified result rate
- policy compliance
- reproducibility
- unexplained deviation rate
- tool error rate
- recovery success
- quarantine events

The initial system should store **raw evidence first**.

A composite trust score is introduced only after benchmark data exists.

No arbitrary production score should be presented as scientifically validated.

---

# 9. Isaac Transparency / Control Index

The index is an experimental benchmark, not a claim of objective consciousness measurement.

Initial dimensions:

### T — Observability
How much relevant execution state can be reconstructed?

### C — Causal coverage
How much of a decision chain has traceable evidence?

### G — Governance
How consistently are capability/policy constraints enforced?

### S — Stability
How reproducible is behavior under controlled conditions?

### R — Recovery
How reliably does the system detect, correct and verify failures?

A first experimental score:

```
ITI = wT*T + wC*C + wG*G + wS*S + wR*R
```

Weights remain configurable and are not declared scientifically canonical until validated.

---

# 10. Benchmark Program

Create:

```
evals/isaac20/
  scenarios/
  metrics/
  runners/
  baselines/
  reports/
```

Initial scenarios:

- context confusion
- hallucinated tool
- permission violation
- unauthorized write
- unauthorized execution
- provider failure
- goal drift
- recursive failure
- memory inconsistency
- watchdog recovery
- quarantine
- root-cause tracing
- verified recovery

Each scenario must define:

- initial state
- task
- injected fault, if any
- expected policy
- observable events
- success criteria
- recovery criteria
- evidence required

---

# 11. Ablation Study

To establish whether Isaac components actually improve behavior:

```
Baseline Agent
Baseline + R/W/X
Baseline + Causal Memory
Baseline + Guardrail
Baseline + Recovery
Full Isaac 2.0
```

Compare:

- failure rate
- unauthorized action rate
- recovery rate
- time to recovery
- trace completeness
- reproducibility
- false positive/negative policy decisions

This is mandatory before making comparative product claims.

---

# 12. Compliance Evidence Layer

Isaac must not claim automatic legal compliance.

Instead it generates technical evidence supporting governance processes.

Potential evidence:

- decision records
- capability decisions
- human approvals
- policy violations
- intervention events
- provider changes
- recovery events
- audit integrity metadata
- benchmark results

Target output:

```
Isaac Governance Evidence Package
---------------------------------
System identity
Model/provider inventory
Risk controls
Capability policies
Decision records
Intervention records
Audit evidence
Evaluation results
Recovery evidence
Configuration snapshot
```

---

# 13. SDK Target

Target developer experience:

```python
from isaac import AgentRuntime

agent = AgentRuntime(
    audit=True,
    causal_memory=True,
    watchdog=True,
)

result = agent.run(task)
```

Capability declaration:

```python
agent.policy.allow(
    resource="filesystem:/workspace",
    read=True,
    write=True,
    execute=False,
)
```

Trace:

```python
trace = agent.trace(result.task_id)
root = agent.root_cause(result.task_id)
```

These are target interfaces, not immediate implementation requirements.

---

# 14. CLI Target

```
isaac init
isaac run
isaac audit
isaac trace <task-id>
isaac root-cause <task-id>
isaac capabilities
isaac quarantine <provider>
isaac benchmark
isaac report
```

Implement only after stable Python interfaces exist.

---

# 15. Dashboard Target

Initial dashboard views:

1. Agent health
2. Capability matrix
3. Active tasks
4. Decision timeline
5. Causal trace
6. Provider trust/evidence
7. Quarantine state
8. Benchmark results
9. Governance evidence

No dashboard rewrite is required during the first implementation milestones.

---

# 16. Implementation Tracks

## Track A — Architecture Contract

Deliverables:
- 2.0 architecture document
- domain vocabulary
- event schema
- capability model specification
- compatibility rules

DoD:
- no duplicated authority
- existing tests remain green

## Track B — R/W/X

Deliverables:
- capability data model
- evaluator
- policy adapter
- capability transition events
- tests

DoD:
- read/write/execute decisions are deterministic
- every decision has an evidence record
- existing privilege/security gates remain authoritative

## Track C — Causal Memory

Status: **B3.2 in progress**

Deliverables:
- causal node/edge schema
- normalized AuditLog + DecisionTrace event adapter
- evidence-backed relationship inference
- graph query API
- root-cause candidate engine
- verification state

Completed:
- **B3.1:** normalized event schema with immutable source preservation
- **B3.2:** deterministic explicit relationship edges for `derived_from`, `depends_on`, `caused_by`, `triggered`, `authorized_by`, `blocked_by`, `corrected_by`, `verified_by`
- temporal adjacency remains `OBSERVED` only
- cross-task explicit references are rejected
- unknown event references are ignored rather than inferred

DoD:
- a failed task can produce a reproducible causal trace from recorded events
- every non-observational causal edge has explicit evidence

## Track D — Cybernetic Guardrail

Deliverables:
- provider trust state
- capability degradation
- quarantine state machine
- watchdog integration
- recovery verification

DoD:
- failing provider loses W/X according to policy
- diagnostic R access remains available where policy permits
- restoration requires verification

## Track E — Metrics

Deliverables:
- metric definitions
- data collectors
- benchmark scenarios
- baseline runner
- ITI experimental report

DoD:
- repeatable benchmark runs
- machine-readable results
- no unsupported superiority claims

## Track F — Governance Evidence

Deliverables:
- evidence schema
- report generator
- configuration snapshots
- intervention/recovery reports

DoD:
- complete technical evidence package for a benchmark run

## Track G — SDK / CLI

Deliverables:
- stable Python API
- CLI
- examples
- developer documentation

DoD:
- third-party developer can instrument an agent without understanding Isaac internals

## Track H — Product / Investor Demo

Deliverables:
- controlled failure demo
- baseline-vs-Isaac comparison
- causal trace visualization
- quarantine demonstration
- benchmark report

DoD:
- 2–3 minute demo communicates the value without philosophical assumptions

---

# 17. Non-Negotiable Engineering Rules

1. Never rewrite the kernel wholesale.
2. Never create a second privilege authority.
3. Never treat an inferred causal explanation as a fact without verification.
4. Never claim an empirical benchmark result before running it.
5. Never claim legal compliance automatically.
6. Never weaken existing safety gates to demonstrate autonomy.
7. Keep new 2.0 capabilities behind explicit interfaces/feature flags where compatibility requires it.
8. Preserve append-only audit evidence.
9. Every autonomous intervention must be auditable.
10. Every recovery must end in verification or an explicit failure state.
11. Never modify `main` directly.
12. Every milestone must have executable tests/evals.

---

# 18. Definition of Done — Isaac 2.0 MVP

Isaac 2.0 MVP is complete when one controlled autonomous task can demonstrate:

```
Intent
  ↓
Policy
  ↓
R/W/X authorization
  ↓
Execution
  ↓
Immutable audit events
  ↓
Decision trace
  ↓
Injected failure
  ↓
Watchdog detection
  ↓
Provider/capability degradation
  ↓
Causal root-cause analysis
  ↓
Corrective action
  ↓
Verification
  ↓
Benchmark result
```

The entire sequence must be reproducible from recorded evidence.

---

# 19. First Implementation Sequence

### Milestone 2.0-A0
Freeze and document baseline.

### Milestone 2.0-A1
Define canonical event and capability schemas.

### Milestone 2.0-B1
Implement R/W/X capability model behind a feature flag.

### Milestone 2.0-B2
Integrate capability decisions with existing privilege/security policy.

### Milestone 2.0-C1
Map existing DecisionTrace + AuditLog into causal events.

### Milestone 2.0-C2
Implement causal graph reconstruction.

### Milestone 2.0-D1
Implement provider capability degradation.

### Milestone 2.0-D2
Connect degradation to watchdog and quarantine.

### Milestone 2.0-E1
Implement first benchmark scenarios.

### Milestone 2.0-E2
Implement ITI experimental metrics.

### Milestone 2.0-F1
Generate governance evidence package.

### Milestone 2.0-G1
Stabilize SDK.

### Milestone 2.0-H1
Build investor demonstration.

---

# 20. Immediate Next Action

The next coding step is **A0**, not implementation of R/W/X yet.

A0 must:

1. capture the current baseline commit;
2. inventory relevant modules;
3. map the runtime flow;
4. identify existing event/trace schemas;
5. identify integration points;
6. define compatibility constraints;
7. create the first 2.0 architecture/evidence tests;
8. record the baseline validation commands and results.

Only after A0 is complete may B1 begin.

---

## Strategic positioning

Isaac should ultimately be positioned as:

> **A control and trust runtime for autonomous AI agents.**

Not:

> an AI consciousness product.

The R/W/X model is the underlying architectural theory.

The commercial product is:

**Observe → Authorize → Execute → Explain → Recover.**
