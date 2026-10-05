# Isaac 2.0 — B3 Causal Event Schema

**Status:** normative first-stage schema

## Source-of-truth rule

The append-only AuditLog and existing DecisionTrace remain authoritative evidence. B3 derives normalized events from them; it does not rewrite, delete, or replace source events.

## Canonical node types

Intent, Context, Plan, Assumption, Observation, ToolCall, ProviderResponse, PolicyDecision, Action, Result, Error, Intervention, Recovery, Verification.

## Canonical edge types

derived_from, depends_on, caused_by, triggered, observed, authorized_by, blocked_by, corrected_by, verified_by.

## Evidence rule

The initial graph builder creates only "observed" edges based on temporal sequence within the same task. These edges are explicitly labeled "temporal_sequence" evidence and must not be interpreted as verified causation.

caused_by, authorized_by, blocked_by, corrected_by, and verified_by require stronger event-level evidence and will be introduced only when the corresponding source relationships are explicit and testable.

## Normalized event fields

Each event contains:

- event ID
- task ID
- node type
- timestamp
- source
- original event name
- original evidence payload
- sequence

The normalized representation is schema version "isaac.causal_graph.v1".

## B3 first-stage exit criteria

- AuditLog records normalize without mutation.
- DecisionTrace entries normalize without mutation.
- Known policy/tool/execution/recovery events map deterministically.
- Cross-task events never receive temporal edges.
- No inferred causal relationship is presented as proven.
- Dedicated unit tests execute in CI.
