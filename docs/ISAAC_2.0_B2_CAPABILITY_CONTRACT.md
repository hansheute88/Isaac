# Isaac 2.0 — B2 Capability Contract

**Status:** normative implementation contract

## Purpose

R/W/X is an additive capability contract. It describes what a task may request for a resource. It does not replace privilege, security policy, confirmation, or constitution gates.

## Canonical request

```json
{
  "resource": "filesystem:/workspace",
  "capability": "write",
  "reason": "task-declared capability"
}
```

Canonical values are `read`, `write`, and `execute`.

## Decision semantics

- Explicit policy grants are deterministic.
- Missing policy means implicit deny.
- Decisions carry resource, capability, principal, reason, task ID, policy source, and policy version.
- Every evaluated request is emitted through `AuditLog.capability`.
- A denied declared capability blocks the task before execution.
- Existing legacy gates remain authoritative.
- R/W/X never escalates privilege or owner authorization.

## Compatibility

Tasks without `required_capabilities` preserve the existing execution path. Registry persistence is intentionally deferred.

## Kernel integration (live path)

The kernel declares no capability groups such as `tools` or `companions` — only canonical
`capability:resource` entries are valid. Instead, the executor emits an advisory decision at
the real tool boundary (`mode="advisory"`, `declared=False`): it is audited and attached to
the decision trace, but it never blocks. Tool eligibility remains with `tool_policy`.
Opt-out: `ISAAC_RWX_ADVISORY=0`.

Enforcement (`mode="enforced"`) applies only to explicitly declared capabilities (dict form)
and requires a registered policy; without one the canonical implicit deny blocks the tool.

## Safety invariant

An R/W/X execute grant cannot authorize an operation rejected by `privilege.py`, `security_policy.py`, `constitution.py`, or another authoritative gate.

## B2 exit criteria

B2 is complete only when deterministic decisions, blocking behavior, audit/trace evidence, compatibility tests, and the dedicated CI test are all green on the final branch head.
