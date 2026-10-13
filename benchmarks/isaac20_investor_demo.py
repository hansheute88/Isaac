"""Isaac 2.0 H1 — reproducible investor demonstration contract.

The demo is evidence-first: it executes the existing E1/E2/E3 benchmark
contracts plus a real R/W/X authorization decision, then packages their actual
evidence into one presentation-ready result. It does not create a second
execution authority and does not claim general superiority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from benchmarks.isaac20_ablation import run_e3_benchmark
from benchmarks.isaac20_fault_injection import run_e1_benchmark
from benchmarks.isaac20_governance import (
    build_governance_evidence,
    verify_governance_evidence,
)
from benchmarks.isaac20_metrics import run_e2_metrics
from isaac_capabilities import Capability, CapabilityRequest, RWXRegistry, evaluate_with_audit


@dataclass(frozen=True)
class DemoStep:
    name: str
    status: str
    evidence: str


DEMO_SCHEMA = "isaac20-investor-demo-v2"


def _authorization_evidence() -> dict[str, Any]:
    """Exercise the real R/W/X authorization boundary with implicit deny."""
    registry = RWXRegistry()
    decision = evaluate_with_audit(
        registry,
        CapabilityRequest(
            resource="benchmark:investor-demo",
            capability=Capability.EXECUTE,
            principal="isaac-demo",
            reason="demonstrate unauthorized execution denial",
            task_id="h1-investor-demo",
        ),
    )
    return decision.as_dict()


def _verified_fault_evidence(e1_report: Mapping[str, Any]) -> dict[str, Any]:
    """Extract one real verified E1 lifecycle, preserving its event IDs."""
    scenario = next(
        (
            item
            for item in e1_report.get("scenarios", [])
            if item.get("evidence", {}).get("final_state") == "verified"
        ),
        None,
    )
    if scenario is None:
        return {"fault_injected": False, "causal_evidence": {}}

    evidence = scenario.get("evidence", {})
    causal_ids = {
        key: evidence.get(key, "")
        for key in (
            "failure_event_id",
            "intervention_event_id",
            "recovery_event_id",
            "verification_event_id",
            "verification_source_event_id",
        )
    }
    return {
        "fault_injected": True,
        "causal_evidence": causal_ids,
        "scenario": scenario.get("scenario"),
        "final_state": evidence.get("final_state"),
        "provider_quarantined": evidence.get("provider_quarantined"),
    }


def build_demo_contract(
    *,
    unauthorized: Mapping[str, Any],
    fault: Mapping[str, Any],
    recovery: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a machine-readable five-stage investor demo from real evidence."""
    governance_valid = verify_governance_evidence(governance)
    fault_ids = fault.get("causal_evidence", {})
    steps = [
        DemoStep(
            "observe",
            "PASS" if unauthorized.get("audit_event_id") else "FAIL",
            "authorization decision is auditable",
        ),
        DemoStep(
            "authorize",
            "PASS" if unauthorized.get("allowed") is False else "FAIL",
            "unauthorized capability is denied",
        ),
        DemoStep(
            "execute",
            "PASS" if fault.get("fault_injected") else "FAIL",
            "controlled fault injection exercises execution failure",
        ),
        DemoStep(
            "explain",
            "PASS"
            if all(
                fault_ids.get(key)
                for key in ("failure_event_id", "intervention_event_id")
            )
            else "FAIL",
            "failure and intervention carry explicit event evidence",
        ),
        DemoStep(
            "recover",
            "PASS"
            if recovery.get("verified") is True and governance_valid
            else "FAIL",
            "recovery is verified and the evidence package integrity checks",
        ),
    ]
    passed = all(step.status == "PASS" for step in steps)
    return {
        "schema_version": DEMO_SCHEMA,
        "title": "Isaac 2.0 — Observe → Authorize → Execute → Explain → Recover",
        "claim_scope": "engineering_demonstration",
        "disclaimer": (
            "This demonstration shows implemented control contracts and "
            "reproducible evidence. It is not a legal certification or a "
            "general superiority claim about arbitrary AI agents."
        ),
        "steps": [asdict(step) for step in steps],
        "governance_evidence": {
            "schema_version": governance.get("schema_version"),
            "evidence_hash": governance.get("integrity", {}).get("evidence_hash"),
            "integrity_verified": governance_valid,
        },
        "evidence": {
            "authorization_event_id": unauthorized.get("audit_event_id"),
            "failure_event_id": fault_ids.get("failure_event_id"),
            "intervention_event_id": fault_ids.get("intervention_event_id"),
            "recovery_event_id": fault_ids.get("recovery_event_id"),
            "verification_event_id": fault_ids.get("verification_event_id"),
        },
        "passed": passed,
    }


def run_investor_demo(*, e2_repetitions: int = 3) -> dict[str, Any]:
    """Execute the real benchmark contracts and assemble one H1 demo result."""
    if e2_repetitions < 1:
        raise ValueError("e2_repetitions must be >= 1")

    e1 = run_e1_benchmark()
    e2 = run_e2_metrics(repetitions=e2_repetitions)
    e3 = run_e3_benchmark()
    unauthorized = _authorization_evidence()
    fault = _verified_fault_evidence(e1)
    recovery = {
        "verified": fault.get("final_state") == "verified"
        and fault.get("provider_quarantined") is False
    }
    governance = build_governance_evidence(
        e1_report=e1,
        e2_report=e2,
        e3_report=e3,
        capability_decisions=[unauthorized],
        config_snapshot={
            "demo_schema": DEMO_SCHEMA,
            "e2_repetitions": e2_repetitions,
        },
        system_identity={"component": "isaac20-investor-demo"},
    )
    contract = build_demo_contract(
        unauthorized=unauthorized,
        fault=fault,
        recovery=recovery,
        governance=governance,
    )
    return {
        "demo": contract,
        "benchmarks": {"e1": e1, "e2": e2, "e3": e3},
        "governance": governance,
        "summary": render_demo_summary(contract),
    }


def render_demo_summary(contract: Mapping[str, Any]) -> str:
    """Return a concise presentation-ready summary."""
    lines = [
        str(contract.get("title", "Isaac 2.0")),
        f"Result: {'PASS' if contract.get('passed') else 'FAIL'}",
    ]
    for step in contract.get("steps", []):
        lines.append(f"{step['name'].upper():9} {step['status']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json

    print(json.dumps(run_investor_demo(), indent=2, sort_keys=True))
