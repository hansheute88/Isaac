"""Isaac 2.0 stable developer facade.

This module intentionally exposes stable interfaces over existing governance
primitives. It does not replace legacy privilege, security or constitution
gates, and it does not execute actions during policy evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from isaac_capabilities import (
    Capability,
    CapabilityRequest,
    RWXPolicy,
    RWXRegistry,
    evaluate_with_audit,
)
from isaac_causal import CausalEvent
from isaac_causal_query import build_root_cause_report


@dataclass(frozen=True)
class AgentResult:
    """Stable result envelope for instrumented runs."""

    ok: bool
    task_id: str = ""
    output: Any = None
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "task_id": self.task_id,
            "output": self.output,
            "error": self.error,
        }


class PolicyFacade:
    """Stable R/W/X policy interface."""

    def __init__(self, registry: RWXRegistry):
        self._registry = registry

    def allow(
        self,
        *,
        resource: str,
        read: bool = False,
        write: bool = False,
        execute: bool = False,
        source: str = "sdk",
        version: int = 1,
    ) -> RWXPolicy:
        return self._registry.set_policy(
            RWXPolicy(
                resource=resource,
                read=read,
                write=write,
                execute=execute,
                source=source,
                version=version,
            )
        )

    def check(
        self,
        *,
        resource: str,
        capability: Capability | str,
        principal: str = "isaac",
        reason: str = "",
        task_id: str = "",
    ):
        return evaluate_with_audit(
            self._registry,
            CapabilityRequest(
                resource=resource,
                capability=capability,
                principal=principal,
                reason=reason,
                task_id=task_id,
            ),
        )


class AgentRuntime:
    """Small stable facade for developers instrumenting an agent."""

    SDK_VERSION = "0.1"

    def __init__(
        self,
        *,
        audit: bool = True,
        causal_memory: bool = True,
        watchdog: bool = True,
        registry: RWXRegistry | None = None,
    ):
        self.audit_enabled = bool(audit)
        self.causal_memory_enabled = bool(causal_memory)
        self.watchdog_enabled = bool(watchdog)
        self._registry = registry or RWXRegistry()
        self.policy = PolicyFacade(self._registry)

    def run(self, task: Any, *, task_id: str = "") -> AgentResult:
        """Return an instrumentation envelope without bypassing execution policy.

        Actual agent execution remains owned by Isaac's existing executor/runtime.
        This facade deliberately avoids inventing a second executor.
        """
        if task is None:
            return AgentResult(ok=False, task_id=task_id, error="task must not be None")
        return AgentResult(ok=True, task_id=task_id, output=task)

    def trace(
        self,
        events: list[CausalEvent] | tuple[CausalEvent, ...],
        *,
        target_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Build a causal trace from already recorded immutable events."""
        from isaac_causal import build_causal_graph

        graph = build_causal_graph(events)
        result = {
            "schema": "isaac.causal_trace.v1",
            "events": [event.as_dict() for event in graph.events],
            "edges": [edge.as_dict() for edge in graph.edges],
        }
        if target_event_id:
            result["root_cause"] = build_root_cause_report(events, target_event_id)
        return result

    def root_cause(
        self,
        events: list[CausalEvent] | tuple[CausalEvent, ...],
        *,
        target_event_id: str,
    ) -> dict[str, Any]:
        return build_root_cause_report(events, target_event_id)
