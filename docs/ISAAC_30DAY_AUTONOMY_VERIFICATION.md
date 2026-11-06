# Isaac 30-Day Autonomy — Verification Contract v1

This document defines the first machine-checkable acceptance layer for the 30-day autonomy program.

## Required evidence identifiers

A valid autonomous cycle should expose or be reconstructable from:
- cycle_id
- decision/authorization evidence
- execution/result evidence
- evaluation evidence
- learning evidence when learning occurred
- goal/subgoal binding when applicable

## Required invariants

- authorization precedes governed execution;
- denied actions do not execute;
- learning records reference real research/task evidence;
- interests reference an owner-aligned derivation chain;
- manual state mutations remain zero during the official proof run;
- final evidence is reproducible from the declared source revision and manifest.

## Gate states

- BASELINE: architecture and governance contracts available.
- CYCLE: autonomous cycle evidence reconstructable.
- LEARNING: measurable learning effect demonstrated.
- INTEREST: bounded interest derivation demonstrated.
- PREFLIGHT: 24h/48h/72h gates passed.
- PROOF: official 30-day run completed.
- FINAL: independent evidence verification passed.

No later gate may be marked passed if an earlier mandatory gate is failed.
