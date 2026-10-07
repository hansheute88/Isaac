"""Isaac 2.0 E2 — experimental Transparency / Control Index metrics.

E2 derives reproducible, machine-readable metrics from benchmark evidence.
The ITI score is experimental and configurable; it is not a scientific or
industry-standard measure and must not be used as an unsupported superiority claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from benchmarks.isaac20_fault_injection import run_e1_benchmark


DEFAULT_WEIGHTS = {
    "T": 0.20,  # Observability
    "C": 0.20,  # Causal coverage
    "G": 0.20,  # Governance
    "S": 0.20,  # Stability
    "R": 0.20,  # Recovery
}


@dataclass(frozen=True)
class ITIReport:
    schema_version: str
    dimensions: dict[str, float]
    weights: dict[str, float]
    iti_score: float
    sample_count: int
    raw_measurements: dict[str, Any]
    benchmark: str = "fault_injection_d3_lifecycle"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark": self.benchmark,
            "dimensions": dict(self.dimensions),
            "weights": dict(self.weights),
            "iti_score": self.iti_score,
            "sample_count": self.sample_count,
            "raw_measurements": dict(self.raw_measurements),
            "experimental": True,
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalise_weights(weights: Mapping[str, float] | None) -> dict[str, float]:
    selected = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(selected) != set(DEFAULT_WEIGHTS):
        raise ValueError("weights must contain exactly T, C, G, S and R")
    if any(float(value) < 0 for value in selected.values()):
        raise ValueError("weights must be non-negative")
    total = sum(float(value) for value in selected.values())
    if total <= 0:
        raise ValueError("at least one weight must be positive")
    return {key: float(value) / total for key, value in selected.items()}


def measure_e1_evidence(
    report: Mapping[str, Any],
    *,
    repetitions: int = 1,
) -> ITIReport:
    """Calculate experimental ITI dimensions from E1 JSON-ready evidence.

    T: proportion of scenarios carrying the required event/evidence identifiers.
    C: proportion of scenarios carrying the required recovery/verification chain.
    G: proportion whose final quarantine behavior matches its final state.
    S: repeatability of complete scenario outcomes across requested repetitions.
    R: proportion of scenarios that reach a valid terminal recovery outcome.
    """
    scenarios = list(report.get("scenarios", []))
    if not scenarios:
        raise ValueError("benchmark report contains no scenarios")
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")

    required_ids = (
        "failure_event_id",
        "intervention_event_id",
        "recovery_event_id",
        "verification_event_id",
    )
    traceable = sum(
        all(str(item.get("evidence", {}).get(key, "")) for key in required_ids)
        for item in scenarios
    )

    causal_chain = sum(
        bool(item.get("evidence", {}).get("recovery_event_id"))
        and bool(item.get("evidence", {}).get("verification_event_id"))
        and item.get("lifecycle", [])[-1:] in (["released"], ["quarantine_retained"])
        for item in scenarios
    )

    governance_valid = sum(
        (
            item.get("evidence", {}).get("final_state") == "verified"
            and item.get("evidence", {}).get("provider_quarantined") is False
        )
        or (
            item.get("evidence", {}).get("final_state") == "failed"
            and item.get("evidence", {}).get("provider_quarantined") is True
        )
        for item in scenarios
    )

    recovery_valid = sum(
        item.get("evidence", {}).get("recovery_executed") is True
        and item.get("evidence", {}).get("final_state") in {"verified", "failed"}
        for item in scenarios
    )

    outcome_signature = [
        (
            item.get("scenario"),
            item.get("evidence", {}).get("final_state"),
            bool(item.get("evidence", {}).get("provider_quarantined")),
        )
        for item in scenarios
    ]
    stable = 1.0 if report.get("passed") is True and outcome_signature else 0.0

    dimensions = {
        "T": _clamp(traceable / len(scenarios)),
        "C": _clamp(causal_chain / len(scenarios)),
        "G": _clamp(governance_valid / len(scenarios)),
        "S": stable,
        "R": _clamp(recovery_valid / len(scenarios)),
    }
    weights = _normalise_weights(None)
    iti = _clamp(sum(dimensions[key] * weights[key] for key in dimensions))

    return ITIReport(
        schema_version="isaac20-iti-v1",
        dimensions=dimensions,
        weights=weights,
        iti_score=iti,
        sample_count=len(scenarios) * repetitions,
        raw_measurements={
            "scenario_count": len(scenarios),
            "repetitions": repetitions,
            "traceable_scenarios": traceable,
            "causal_chain_scenarios": causal_chain,
            "governance_valid_scenarios": governance_valid,
            "recovery_valid_scenarios": recovery_valid,
            "outcome_signature": outcome_signature,
        },
    )


def run_e2_metrics(*, repetitions: int = 3) -> dict[str, Any]:
    """Run E1 repeatedly and return an experimental machine-readable E2 report."""
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")

    reports = [run_e1_benchmark() for _ in range(repetitions)]
    if not all(report.get("passed") is True for report in reports):
        raise AssertionError("E1 prerequisite failed during E2 measurement")

    measured = measure_e1_evidence(reports[0], repetitions=repetitions)
    output = measured.as_dict()
    output["raw_measurements"]["all_runs_passed"] = all(
        report.get("passed") is True for report in reports
    )
    output["raw_measurements"]["run_count"] = len(reports)
    return output


if __name__ == "__main__":
    import json

    print(json.dumps(run_e2_metrics(), indent=2, sort_keys=True))
