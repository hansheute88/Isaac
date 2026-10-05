"""Isaac 2.0 normalized causal event schema.

Causal memory is derived from immutable audit evidence and DecisionTrace data.
This module does not replace either source and does not invent causal facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class CausalNodeType(str, Enum):
    INTENT = "Intent"
    CONTEXT = "Context"
    PLAN = "Plan"
    ASSUMPTION = "Assumption"
    OBSERVATION = "Observation"
    TOOL_CALL = "ToolCall"
    PROVIDER_RESPONSE = "ProviderResponse"
    POLICY_DECISION = "PolicyDecision"
    ACTION = "Action"
    RESULT = "Result"
    ERROR = "Error"
    INTERVENTION = "Intervention"
    RECOVERY = "Recovery"
    VERIFICATION = "Verification"


class CausalEdgeType(str, Enum):
    DERIVED_FROM = "derived_from"
    DEPENDS_ON = "depends_on"
    CAUSED_BY = "caused_by"
    TRIGGERED = "triggered"
    OBSERVED = "observed"
    AUTHORIZED_BY = "authorized_by"
    BLOCKED_BY = "blocked_by"
    CORRECTED_BY = "corrected_by"
    VERIFIED_BY = "verified_by"


@dataclass(frozen=True)
class CausalEvent:
    event_id: str
    task_id: str
    node_type: CausalNodeType
    timestamp_ms: int
    source: str
    event: str
    data: Mapping[str, Any] = field(default_factory=dict)
    sequence: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "node_type": self.node_type.value,
            "timestamp_ms": self.timestamp_ms,
            "source": self.source,
            "event": self.event,
            "data": dict(self.data),
            "sequence": self.sequence,
        }


@dataclass(frozen=True)
class CausalEdge:
    source_event_id: str
    target_event_id: str
    edge_type: CausalEdgeType
    evidence: str = "sequence"

    def as_dict(self) -> dict[str, str]:
        return {
            "source_event_id": self.source_event_id,
            "target_event_id": self.target_event_id,
            "edge_type": self.edge_type.value,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class CausalGraph:
    events: tuple[CausalEvent, ...] = ()
    edges: tuple[CausalEdge, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "isaac.causal_graph.v1",
            "events": [e.as_dict() for e in self.events],
            "edges": [e.as_dict() for e in self.edges],
        }


_AUDIT_MAP = {
    "steffen_input": CausalNodeType.INTENT,
    "task": CausalNodeType.RESULT,
    "capability": CausalNodeType.POLICY_DECISION,
    "privilege": CausalNodeType.POLICY_DECISION,
    "action": CausalNodeType.ACTION,
    "error": CausalNodeType.ERROR,
    "memory": CausalNodeType.OBSERVATION,
    "internet": CausalNodeType.OBSERVATION,
    "confirmation": CausalNodeType.POLICY_DECISION,
    "decision_trace": CausalNodeType.OBSERVATION,
    "isaac_output": CausalNodeType.RESULT,
}

_TRACE_MAP = {
    "capability_decision": CausalNodeType.POLICY_DECISION,
    "tool_selected": CausalNodeType.TOOL_CALL,
    "tool_call": CausalNodeType.TOOL_CALL,
    "execution_succeeded": CausalNodeType.RESULT,
    "execution_failed": CausalNodeType.ERROR,
    "constitution_blocked": CausalNodeType.POLICY_DECISION,
    "provider_failed": CausalNodeType.ERROR,
    "provider_switched": CausalNodeType.INTERVENTION,
    "recovery_started": CausalNodeType.RECOVERY,
    "recovery_verified": CausalNodeType.VERIFICATION,
    "context_appended": CausalNodeType.CONTEXT,
}


def _node_type(source: str, event: str) -> CausalNodeType:
    return (_TRACE_MAP if source == "decision_trace" else _AUDIT_MAP).get(
        event, CausalNodeType.OBSERVATION
    )


def normalize_audit_events(records: Iterable[Mapping[str, Any]]) -> list[CausalEvent]:
    """Normalize raw append-only AuditLog records without mutating them."""
    out: list[CausalEvent] = []
    for index, record in enumerate(records, 1):
        typ = str(record.get("typ") or "unknown")
        task_id = str(record.get("task_id") or "")
        event_id = str(record.get("event_id") or f"audit-{index}")
        ts = record.get("ms")
        try:
            timestamp_ms = int(ts or 0)
        except (TypeError, ValueError):
            timestamp_ms = 0
        data = {
            k: v for k, v in record.items()
            if k not in {"typ", "task_id", "ms", "ts"}
        }
        out.append(CausalEvent(
            event_id=event_id,
            task_id=task_id,
            node_type=_node_type("audit", typ),
            timestamp_ms=timestamp_ms,
            source="audit",
            event=typ,
            data=data,
            sequence=index,
        ))
    return out


def normalize_trace_entries(
    entries: Iterable[Mapping[str, Any]], task_id: str = ""
) -> list[CausalEvent]:
    """Normalize existing DecisionTrace entries without changing their schema."""
    out: list[CausalEvent] = []
    for index, entry in enumerate(entries, 1):
        event = str(entry.get("event") or "unknown")
        data = dict(entry.get("data") or {})
        sequence = int(entry.get("sequence") or index)
        ts = float(entry.get("ts") or 0.0)
        out.append(CausalEvent(
            event_id=f"trace-{task_id or 'unknown'}-{sequence}",
            task_id=task_id,
            node_type=_node_type("decision_trace", event),
            timestamp_ms=int(ts * 1000),
            source="decision_trace",
            event=event,
            data=data,
            sequence=sequence,
        ))
    return out



# Explicit relationships require an event-id reference in the evidence.
_EXPLICIT_RELATION_KEYS = {
    "derived_from": CausalEdgeType.DERIVED_FROM,
    "derived_from_event_id": CausalEdgeType.DERIVED_FROM,
    "depends_on": CausalEdgeType.DEPENDS_ON,
    "depends_on_event_id": CausalEdgeType.DEPENDS_ON,
    "caused_by": CausalEdgeType.CAUSED_BY,
    "caused_by_event_id": CausalEdgeType.CAUSED_BY,
    "triggered_by": CausalEdgeType.TRIGGERED,
    "triggered_by_event_id": CausalEdgeType.TRIGGERED,
    "authorized_by": CausalEdgeType.AUTHORIZED_BY,
    "authorized_by_event_id": CausalEdgeType.AUTHORIZED_BY,
    "blocked_by": CausalEdgeType.BLOCKED_BY,
    "blocked_by_event_id": CausalEdgeType.BLOCKED_BY,
    "corrected_by": CausalEdgeType.CORRECTED_BY,
    "corrected_by_event_id": CausalEdgeType.CORRECTED_BY,
    "verified_by": CausalEdgeType.VERIFIED_BY,
    "verified_by_event_id": CausalEdgeType.VERIFIED_BY,
}

def build_explicit_relationship_edges(events: Iterable[CausalEvent]) -> tuple[CausalEdge, ...]:
    """Build only relationships explicitly declared by event evidence."""
    ordered = tuple(events)
    by_id = {event.event_id: event for event in ordered}
    edges: list[CausalEdge] = []
    for target in ordered:
        for key, edge_type in _EXPLICIT_RELATION_KEYS.items():
            reference = target.data.get(key)
            if not isinstance(reference, str):
                continue
            reference = reference.strip()
            if not reference or reference not in by_id:
                continue
            source = by_id[reference]
            if source.event_id == target.event_id:
                continue
            if source.task_id and target.task_id and source.task_id != target.task_id:
                continue
            edges.append(CausalEdge(
                source_event_id=source.event_id,
                target_event_id=target.event_id,
                edge_type=edge_type,
                evidence=f"explicit:{key}",
            ))
    unique = {(e.source_event_id, e.target_event_id, e.edge_type.value): e for e in edges}
    return tuple(unique[key] for key in sorted(unique))

def build_causal_graph(events: Iterable[CausalEvent]) -> CausalGraph:
    """Combine temporal observations with explicit evidence relationships."""
    ordered = tuple(sorted(events, key=lambda e: (e.timestamp_ms, e.sequence, e.event_id)))
    sequence_graph = build_sequence_graph(ordered)
    explicit = build_explicit_relationship_edges(ordered)
    edges = sequence_graph.edges + tuple(edge for edge in explicit if edge not in sequence_graph.edges)
    return CausalGraph(events=ordered, edges=edges)

def build_sequence_graph(events: Iterable[CausalEvent]) -> CausalGraph:
    """Build evidence-backed temporal edges, not proven causal claims."""
    ordered = tuple(sorted(
        events, key=lambda e: (e.timestamp_ms, e.sequence, e.event_id)
    ))
    edges = tuple(
        CausalEdge(
            source_event_id=ordered[i - 1].event_id,
            target_event_id=ordered[i].event_id,
            edge_type=CausalEdgeType.OBSERVED,
            evidence="temporal_sequence",
        )
        for i in range(1, len(ordered))
        if ordered[i - 1].task_id == ordered[i].task_id
        and ordered[i - 1].task_id
    )
    return CausalGraph(events=ordered, edges=edges)
