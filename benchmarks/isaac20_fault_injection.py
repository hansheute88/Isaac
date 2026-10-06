"""Isaac 2.0 E1 fault-injection benchmark.

This harness measures the D3 recovery lifecycle instead of merely checking that
individual methods execute. It uses an in-memory provider authority so the
benchmark is deterministic and does not touch production provider state.

Lifecycle:
    injected fault/hang -> intervention/quarantine -> recovery
    -> controlled verification -> verified release OR failed retention
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Callable

from isaac_guardrails import GuardrailController, GuardrailState


class InjectedProviderHang(RuntimeError):
    """Deterministic stand-in for a provider hang/failure."""


class BenchmarkBlacklist:
    """Minimal provider-availability authority for isolated benchmark runs."""

    def __init__(self) -> None:
        self._quarantined: set[str] = set()
        self.events: list[dict[str, Any]] = []

    def quarantine(self, provider: str, *, reason: str = "", source_event_id: str = "") -> None:
        self._quarantined.add(provider)
        self.events.append(
            {
                "event": "quarantine",
                "provider": provider,
                "reason": reason,
                "source_event_id": source_event_id,
            }
        )

    def verify_quarantine(self, provider: str) -> bool:
        self._quarantined.discard(provider)
        self.events.append({"event": "release", "provider": provider})
        return True

    def is_quarantined(self, provider: str) -> bool:
        return provider in self._quarantined


@dataclass
class FaultInjectionResult:
    scenario: str
    fault_mode: str
    passed: bool
    lifecycle: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    failure: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "isaac20-e1-v1",
            "scenario": self.scenario,
            "fault_mode": self.fault_mode,
            "passed": self.passed,
            "lifecycle": list(self.lifecycle),
            "evidence": dict(self.evidence),
            "failure": self.failure,
        }


def run_fault_injection(
    *,
    scenario: str,
    verification_probe: Callable[[], bool],
    fault_mode: str = "provider_hang",
) -> FaultInjectionResult:
    """Run one isolated D3 fault-injection scenario and return JSON-ready evidence."""
    provider = "benchmark-provider"
    failure_event_id = f"e1-{scenario}-failure"
    task_id = f"e1-{scenario}"
    refs: dict[str, str] = {}
    blacklist = BenchmarkBlacklist()
    controller = GuardrailController(blacklist)
    lifecycle = ["fault_injected"]

    try:
        try:
            raise InjectedProviderHang(f"{fault_mode}: injected")
        except InjectedProviderHang as exc:
            lifecycle.append("failure_observed")
            intervention = controller.intervene_provider(
                provider=provider,
                failed_event_id=failure_event_id,
                error=str(exc),
                safety_critical=True,
                task_id=task_id,
            )

        intervention_event_id = controller.last_intervention_event_id(
            f"provider:{provider}"
        )
        lifecycle.append("intervention")
        if intervention.state is not GuardrailState.QUARANTINED:
            raise AssertionError("fault did not enter QUARANTINED state")
        if not blacklist.is_quarantined(provider):
            raise AssertionError("provider was not quarantined")
        if not intervention_event_id:
            raise AssertionError("missing intervention evidence event id")

        lifecycle.append("quarantined")
        recovery_called: list[str] = []
        decision = controller.recover_and_verify_provider(
            provider=provider,
            source_event_id=intervention_event_id,
            reason="E1 controlled recovery",
            recovery_action=lambda: recovery_called.append("recovery"),
            verification_probe=verification_probe,
            task_id=task_id,
            causal_refs=refs,
        )
        lifecycle.append("recovery")
        lifecycle.append("verification")

        expected_verified = bool(decision.state is GuardrailState.VERIFIED)
        if expected_verified:
            lifecycle.append("verified")
            if blacklist.is_quarantined(provider):
                raise AssertionError("verified provider remained quarantined")
            lifecycle.append("released")
        else:
            lifecycle.append("failed")
            if not blacklist.is_quarantined(provider):
                raise AssertionError("failed verification released quarantine")
            lifecycle.append("quarantine_retained")

        evidence = {
            "failure_event_id": failure_event_id,
            "intervention_event_id": intervention_event_id,
            "recovery_event_id": refs.get("guardrail_recovery_event_id", ""),
            "verification_event_id": refs.get("guardrail_verification_event_id", ""),
            "verification_source_event_id": refs.get(
                "guardrail_verification_source_event_id", ""
            ),
            "final_state": decision.state.value,
            "recovery_executed": recovery_called == ["recovery"],
            "provider_quarantined": blacklist.is_quarantined(provider),
            "authority_events": list(blacklist.events),
        }
        return FaultInjectionResult(
            scenario=scenario,
            fault_mode=fault_mode,
            passed=True,
            lifecycle=lifecycle,
            evidence=evidence,
        )
    except Exception as exc:
        return FaultInjectionResult(
            scenario=scenario,
            fault_mode=fault_mode,
            passed=False,
            lifecycle=lifecycle,
            evidence={
                "provider_quarantined": blacklist.is_quarantined(provider),
                "authority_events": list(blacklist.events),
                "refs": dict(refs),
            },
            failure=f"{type(exc).__name__}: {exc}",
        )


def run_e1_benchmark() -> dict[str, Any]:
    """Run both required D3 outcomes: verified release and failed retention."""
    results = [
        run_fault_injection(
            scenario="provider_hang_verified_recovery",
            verification_probe=lambda: True,
        ),
        run_fault_injection(
            scenario="provider_hang_failed_verification",
            verification_probe=lambda: False,
        ),
    ]
    return {
        "schema_version": "isaac20-e1-suite-v1",
        "benchmark": "fault_injection_d3_lifecycle",
        "scenarios": [result.as_dict() for result in results],
        "passed": all(result.passed for result in results),
    }


if __name__ == "__main__":
    print(json.dumps(run_e1_benchmark(), indent=2, sort_keys=True))
