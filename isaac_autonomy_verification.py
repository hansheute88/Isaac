"""Isaac 30-Day Autonomy — Verification Gate Engine.

This module enforces the gate progression rules and Definition of Done criteria
specified in ISAAC_30DAY_AUTONOMY_CONTRACT.md and ISAAC_30DAY_AUTONOMY_VERIFICATION.md.

Gate Progression Sequence:
BASELINE -> CYCLE -> LEARNING -> INTEREST -> PREFLIGHT -> PROOF -> FINAL

Invariants:
1. No later gate may pass if an earlier gate is failed.
2. Manual state mutations must remain zero for official proof run.
3. Every gate evaluation is deterministic and machine-checkable from recorded evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from decision_trace import DecisionTrace
from isaac_autonomy_cycle import validate_cycle
from isaac_autonomy_reconstruction import reconstruct_cycle
from isaac_interest_derivation import validate_interest_derivation
from isaac_learning_causality import validate_learning_record
from benchmarks.isaac20_governance import verify_governance_evidence
from benchmarks.isaac20_governance_f2 import verify_reproducibility_manifest

VERIFICATION_SCHEMA = "isaac.autonomy.verification.v1"

GATE_BASELINE = "BASELINE"
GATE_CYCLE = "CYCLE"
GATE_LEARNING = "LEARNING"
GATE_INTEREST = "INTEREST"
GATE_PREFLIGHT = "PREFLIGHT"
GATE_PROOF = "PROOF"
GATE_FINAL = "FINAL"

GATE_SEQUENCE = [
    GATE_BASELINE,
    GATE_CYCLE,
    GATE_LEARNING,
    GATE_INTEREST,
    GATE_PREFLIGHT,
    GATE_PROOF,
    GATE_FINAL,
]


@dataclass
class AutonomyRunMetrics:
    uptime_days: float = 0.0
    uptime_target_days: float = 30.0
    cycles: list[dict[str, Any]] = field(default_factory=list)
    subgoals_count: int = 0
    research_cycles_count: int = 0
    learning_records: list[dict[str, Any]] = field(default_factory=list)
    interest_derivations: list[dict[str, Any]] = field(default_factory=list)
    unauthorized_actions_count: int = 0
    manual_state_mutations: int = 0
    has_lifecycle_trace: bool = False
    has_provenance_manifest: bool = False
    governance_evidence_package: dict[str, Any] = field(default_factory=dict)
    provenance_manifest: dict[str, Any] = field(default_factory=dict)
    report_exportable: bool = True
    independent_validation_passed: bool = False
    preflight_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "uptime_days": self.uptime_days,
            "uptime_target_days": self.uptime_target_days,
            "cycles": self.cycles,
            "subgoals_count": self.subgoals_count,
            "research_cycles_count": self.research_cycles_count,
            "learning_records": self.learning_records,
            "interest_derivations": self.interest_derivations,
            "unauthorized_actions_count": self.unauthorized_actions_count,
            "manual_state_mutations": self.manual_state_mutations,
            "has_lifecycle_trace": self.has_lifecycle_trace,
            "has_provenance_manifest": self.has_provenance_manifest,
            "governance_evidence_package": self.governance_evidence_package,
            "provenance_manifest": self.provenance_manifest,
            "report_exportable": self.report_exportable,
            "independent_validation_passed": self.independent_validation_passed,
            "preflight_passed": self.preflight_passed,
        }


def evaluate_autonomy_gates(
    metrics: AutonomyRunMetrics | dict[str, Any],
    trace: DecisionTrace | None = None,
) -> dict[str, Any]:
    m = metrics.to_dict() if isinstance(metrics, AutonomyRunMetrics) else dict(metrics or {})

    cycles_list = list(m.get("cycles") or [])
    valid_cycles_count = 0
    for c in cycles_list:
        v = validate_cycle(c) if hasattr(c, "missing_required") else (
            c.get("validation") if isinstance(c.get("validation"), dict) else validate_cycle_data(c)
        )
        if v.get("valid"):
            valid_cycles_count += 1

    if trace is not None:
        entries = trace.to_list()
        cycle_ids = {
            str((e.get("data") or {}).get("cycle_id") or "").strip()
            for e in entries
            if str((e.get("data") or {}).get("cycle_id") or "").strip()
        }
        for cid in cycle_ids:
            reconstructed = reconstruct_cycle(trace, cid)
            if reconstructed.get("valid"):
                valid_cycles_count += 1

    learning_recs = list(m.get("learning_records") or [])
    valid_learning_recs = [r for r in learning_recs if validate_learning_record(r).get("valid")]
    learning_effects_present = any(
        bool(r.get("affected_decision_ids") or getattr(r, "affected_decision_ids", None))
        for r in valid_learning_recs
    )

    interest_derivs = list(m.get("interest_derivations") or [])
    valid_interest_derivs = [d for d in interest_derivs if validate_interest_derivation(d).get("valid")]

    uptime = float(m.get("uptime_days") or 0.0)
    target_uptime = float(m.get("uptime_target_days") or 30.0)
    subgoals = int(m.get("subgoals_count") or 0)
    research_cycles = int(m.get("research_cycles_count") or 0)
    unauthorized = int(m.get("unauthorized_actions_count") or 0)
    mutations = int(m.get("manual_state_mutations") or 0)
    # These gates must be based on supplied evidence, not caller-set booleans.
    has_trace = trace is not None and bool(trace.to_list())
    evidence_package = m.get("governance_evidence_package")
    manifest = m.get("provenance_manifest")
    workflow = manifest.get("workflow", {}) if isinstance(manifest, dict) else {}
    source_revision = str(manifest.get("source_revision") or "") if isinstance(manifest, dict) else ""
    has_manifest = (
        isinstance(evidence_package, dict)
        and isinstance(manifest, dict)
        and bool(re.fullmatch(r"[0-9a-f]{40}", source_revision))
        and bool(str(workflow.get("run_id") or "").strip())
        and bool(str(workflow.get("name") or "").strip())
        and verify_governance_evidence(evidence_package)
        and verify_reproducibility_manifest(manifest, evidence_package=evidence_package)
    )
    exportable = bool(m.get("report_exportable"))
    independent_val = bool(m.get("independent_validation_passed"))
    preflight = bool(m.get("preflight_passed"))

    dod_checks = {
        "1_uptime": uptime >= target_uptime,
        "2_reconstructable_cycles": valid_cycles_count >= 1,
        "3_subgoals": subgoals >= 5,
        "4_research_cycles": research_cycles >= 10,
        "5_learning_effects": len(valid_learning_recs) >= 1,
        "6_interest_derivations": len(valid_interest_derivs) >= 2,
        "7_downstream_effect": learning_effects_present,
        "8_zero_unauthorized_actions": unauthorized == 0,
        "9_zero_manual_state_mutations": mutations == 0,
        "10_lifecycle_trace": has_trace,
        "11_provenance_manifest": has_manifest,
        "12_exportable_report": exportable,
        "13_independent_validation": independent_val,
    }

    gate_evaluations: dict[str, dict[str, Any]] = {}
    passed_gates: list[str] = []
    blocked = False

    # 1. BASELINE
    if not blocked and has_trace and has_manifest:
        gate_evaluations[GATE_BASELINE] = {"passed": True, "reason": "Architecture and governance contracts available"}
        passed_gates.append(GATE_BASELINE)
    else:
        blocked = True
        gate_evaluations[GATE_BASELINE] = {"passed": False, "reason": "Missing lifecycle trace or provenance manifest"}

    # 2. CYCLE
    if not blocked and valid_cycles_count >= 1:
        gate_evaluations[GATE_CYCLE] = {"passed": True, "reason": f"Reconstructable cycles available ({valid_cycles_count})"}
        passed_gates.append(GATE_CYCLE)
    else:
        if not blocked:
            blocked = True
        gate_evaluations[GATE_CYCLE] = {"passed": False, "reason": "No valid reconstructable decision cycles found"}

    # 3. LEARNING
    if not blocked and len(valid_learning_recs) >= 1 and learning_effects_present:
        gate_evaluations[GATE_LEARNING] = {"passed": True, "reason": f"Measurable learning effect demonstrated ({len(valid_learning_recs)} records)"}
        passed_gates.append(GATE_LEARNING)
    else:
        if not blocked:
            blocked = True
        gate_evaluations[GATE_LEARNING] = {"passed": False, "reason": "No valid learning records with downstream effects found"}

    # 4. INTEREST
    if not blocked and len(valid_interest_derivs) >= 2:
        gate_evaluations[GATE_INTEREST] = {"passed": True, "reason": f"Bounded interest derivation demonstrated ({len(valid_interest_derivs)} valid chains)"}
        passed_gates.append(GATE_INTEREST)
    else:
        if not blocked:
            blocked = True
        gate_evaluations[GATE_INTEREST] = {"passed": False, "reason": f"Insufficient valid interest derivation chains ({len(valid_interest_derivs)} < 2)"}

    # 5. PREFLIGHT
    if not blocked and preflight:
        gate_evaluations[GATE_PREFLIGHT] = {"passed": True, "reason": "24h/48h/72h preflight stability gates passed"}
        passed_gates.append(GATE_PREFLIGHT)
    else:
        if not blocked:
            blocked = True
        gate_evaluations[GATE_PREFLIGHT] = {"passed": False, "reason": "Preflight stability gates not passed"}

    # 6. PROOF
    proof_dod_keys = [
        "1_uptime", "2_reconstructable_cycles", "3_subgoals", "4_research_cycles",
        "5_learning_effects", "6_interest_derivations", "7_downstream_effect",
        "8_zero_unauthorized_actions", "9_zero_manual_state_mutations",
        "10_lifecycle_trace", "11_provenance_manifest", "12_exportable_report",
    ]
    proof_passed = not blocked and all(dod_checks[k] for k in proof_dod_keys)
    if proof_passed:
        gate_evaluations[GATE_PROOF] = {"passed": True, "reason": "Official 30-day proof run requirements completed"}
        passed_gates.append(GATE_PROOF)
    else:
        if not blocked:
            blocked = True
        gate_evaluations[GATE_PROOF] = {"passed": False, "reason": "Official proof run criteria incomplete"}

    # 7. FINAL
    if not blocked and independent_val and all(dod_checks.values()):
        gate_evaluations[GATE_FINAL] = {"passed": True, "reason": "Independent evidence verification passed"}
        passed_gates.append(GATE_FINAL)
    else:
        gate_evaluations[GATE_FINAL] = {"passed": False, "reason": "Independent evidence verification incomplete"}

    highest_passed = passed_gates[-1] if passed_gates else None

    return {
        "schema": VERIFICATION_SCHEMA,
        "gate_states": gate_evaluations,
        "passed_gates": passed_gates,
        "highest_passed_gate": highest_passed,
        "dod_status": dod_checks,
        "dod_passed": all(dod_checks.values()),
        "valid_cycles_count": valid_cycles_count,
        "valid_learning_records_count": len(valid_learning_recs),
        "valid_interest_derivations_count": len(valid_interest_derivs),
    }


def validate_cycle_data(c: dict[str, Any]) -> dict[str, Any]:
    from isaac_autonomy_cycle import AutonomyCycle
    cycle = AutonomyCycle(
        cycle_id=str(c.get("cycle_id") or ""),
        goal_id=str(c.get("goal_id") or ""),
        subgoal_id=str(c.get("subgoal_id") or ""),
        intent=str(c.get("intent") or ""),
        authorization_event_id=str(c.get("authorization_event_id") or ""),
        authorization_allowed=(c.get("authorization_allowed") if "authorization_allowed" in c else None),
        authorization_action_id=str(c.get("authorization_action_id") or ""),
        authorization_scope=str(c.get("authorization_scope") or ""),
        execution_action_id=str(c.get("execution_action_id") or ""),
        execution_scope=str(c.get("execution_scope") or ""),
        execution_event_id=str(c.get("execution_event_id") or ""),
        evaluation_event_id=str(c.get("evaluation_event_id") or ""),
        learning_id=str(c.get("learning_id") or ""),
        next_cycle_id=str(c.get("next_cycle_id") or ""),
    )
    return validate_cycle(cycle)
