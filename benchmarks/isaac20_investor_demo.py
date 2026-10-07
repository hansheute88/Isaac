"""Isaac 2.0 H1 — reproducible investor demonstration contract.

The demo is intentionally evidence-first: it packages the public control loop
without pretending that a benchmark result proves general superiority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class DemoStep:
    name: str
    status: str
    evidence: str


DEMO_SCHEMA = "isaac20-investor-demo-v1"


def build_demo_contract(
    *,
    unauthorized: Mapping[str, Any],
    fault: Mapping[str, Any],
    recovery: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a machine-readable five-stage investor demo from evidence."""
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
            "PASS" if fault.get("causal_evidence") else "FAIL",
            "failure carries causal evidence",
        ),
        DemoStep(
            "recover",
            "PASS" if recovery.get("verified") else "FAIL",
            "recovery requires controlled verification",
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
        },
        "passed": passed,
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
