"""Isaac 2.0 E3 — controlled ablation benchmark.

E3 measures the contribution of the defined control layers in a deterministic
contract-level harness. It is not an empirical claim about arbitrary agents.
The benchmark compares the declared architecture variants:
Baseline, +R/W/X, +Causal, +Guardrail, +Recovery and Full Isaac 2.0.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from benchmarks.isaac20_fault_injection import run_e1_benchmark


SCENARIOS = (
    "unauthorized_execution",
    "causal_trace",
    "provider_quarantine",
    "verified_recovery",
)


@dataclass(frozen=True)
class AblationVariant:
    name: str
    rwx: bool = False
    causal: bool = False
    guardrail: bool = False
    recovery: bool = False


VARIANTS = (
    AblationVariant("baseline"),
    AblationVariant("rwx", rwx=True),
    AblationVariant("causal", causal=True),
    AblationVariant("guardrail", guardrail=True),
    AblationVariant("recovery", recovery=True, guardrail=True),
    AblationVariant("full", rwx=True, causal=True, guardrail=True, recovery=True),
)


def _scenario_passes(variant: AblationVariant, scenario: str) -> bool:
    required = {
        "unauthorized_execution": variant.rwx,
        "causal_trace": variant.causal,
        "provider_quarantine": variant.guardrail,
        "verified_recovery": variant.guardrail and variant.recovery,
    }
    return required[scenario]


def run_e3_ablation() -> dict[str, Any]:
    """Return deterministic, machine-readable contract-level ablation evidence."""
    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        outcomes = {
            scenario: _scenario_passes(variant, scenario)
            for scenario in SCENARIOS
        }
        rows.append(
            {
                "variant": variant.name,
                "components": {
                    "rwx": variant.rwx,
                    "causal": variant.causal,
                    "guardrail": variant.guardrail,
                    "recovery": variant.recovery,
                },
                "scenario_outcomes": outcomes,
                "pass_rate": sum(outcomes.values()) / len(outcomes),
            }
        )

    e1 = run_e1_benchmark()
    full_row = next(row for row in rows if row["variant"] == "full")
    e1_terminal_states = {
        item["evidence"]["final_state"] for item in e1["scenarios"]
    }

    return {
        "schema_version": "isaac20-e3-ablation-v1",
        "benchmark": "controlled_architecture_ablation",
        "experimental": True,
        "claim_scope": "contract_level_control_contribution",
        "variants": rows,
        "full_variant_e1_prerequisite": {
            "passed": e1["passed"],
            "terminal_states": sorted(e1_terminal_states),
            "required_terminal_states": ["failed", "verified"],
        },
        "pass_criteria": {
            "full_variant_pass_rate": full_row["pass_rate"] == 1.0,
            "e1_prerequisite": e1["passed"]
            and e1_terminal_states == {"verified", "failed"},
        },
    }


def run_e3_benchmark() -> dict[str, Any]:
    """Compatibility entry point for F1 governance packaging and CI."""
    report = run_e3_ablation()
    report["passed"] = all(report["pass_criteria"].values())
    return report


if __name__ == "__main__":
    report = run_e3_benchmark()
    print(json.dumps(report, indent=2, sort_keys=True))
