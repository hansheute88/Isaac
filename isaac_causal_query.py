"""Isaac 2.0 causal query and root-cause analysis.

Evidence policy:
- OBSERVED edges describe temporal adjacency only.
- Explicit relationship edges are evidence-backed.
- Hypotheses are never promoted to verified causes automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from isaac_causal import CausalEdgeType, CausalEvent, CausalGraph, build_causal_graph


class CausalConfidence(str, Enum):
    OBSERVED = "observed"
    EXPLICIT = "explicit"
    HYPOTHESIS = "hypothesis"
    VERIFIED = "verified"


@dataclass(frozen=True)
class RootCauseCandidate:
    event_id: str
    task_id: str
    event: str
    node_type: str
    confidence: CausalConfidence
    evidence: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "event": self.event,
            "node_type": self.node_type,
            "confidence": self.confidence.value,
            "evidence": list(self.evidence),
        }


_EXPLICIT_CONFIDENCE = {
    CausalEdgeType.CAUSED_BY: CausalConfidence.EXPLICIT,
    CausalEdgeType.TRIGGERED: CausalConfidence.EXPLICIT,
    CausalEdgeType.AUTHORIZED_BY: CausalConfidence.EXPLICIT,
    CausalEdgeType.BLOCKED_BY: CausalConfidence.EXPLICIT,
    CausalEdgeType.CORRECTED_BY: CausalConfidence.EXPLICIT,
    CausalEdgeType.VERIFIED_BY: CausalConfidence.VERIFIED,
    CausalEdgeType.DERIVED_FROM: CausalConfidence.EXPLICIT,
    CausalEdgeType.DEPENDS_ON: CausalConfidence.EXPLICIT,
}


def _event_map(graph: CausalGraph) -> dict[str, CausalEvent]:
    return {event.event_id: event for event in graph.events}


def predecessors(graph: CausalGraph, event_id: str) -> tuple[CausalEvent, ...]:
    """Return explicit/observational predecessors of an event."""
    ids = []
    seen: set[str] = set()
    for edge in graph.edges:
        if edge.target_event_id != event_id or edge.source_event_id in seen:
            continue
        seen.add(edge.source_event_id)
        ids.append(edge.source_event_id)
    events = _event_map(graph)
    return tuple(events[event_id] for event_id in ids if event_id in events)


def successors(graph: CausalGraph, event_id: str) -> tuple[CausalEvent, ...]:
    ids = []
    seen: set[str] = set()
    for edge in graph.edges:
        if edge.source_event_id != event_id or edge.target_event_id in seen:
            continue
        seen.add(edge.target_event_id)
        ids.append(edge.target_event_id)
    events = _event_map(graph)
    return tuple(events[event_id] for event_id in ids if event_id in events)


def _confidence_for_edge(edge_type: CausalEdgeType) -> CausalConfidence:
    return _EXPLICIT_CONFIDENCE.get(edge_type, CausalConfidence.OBSERVED)


def root_cause_candidates(graph: CausalGraph, target_event_id: str) -> tuple[RootCauseCandidate, ...]:
    """Rank direct predecessors without inventing causality from adjacency."""
    events = _event_map(graph)
    candidates = []
    for edge in graph.edges:
        if edge.target_event_id != target_event_id:
            continue
        source = events.get(edge.source_event_id)
        if source is None:
            continue
        confidence = _confidence_for_edge(edge.edge_type)
        candidates.append(
            RootCauseCandidate(
                event_id=source.event_id,
                task_id=source.task_id,
                event=source.event,
                node_type=source.node_type.value,
                confidence=confidence,
                evidence=(edge.evidence,),
            )
        )
    rank = {
        CausalConfidence.VERIFIED: 0,
        CausalConfidence.EXPLICIT: 1,
        CausalConfidence.OBSERVED: 2,
        CausalConfidence.HYPOTHESIS: 3,
    }
    return tuple(sorted(candidates, key=lambda item: (rank[item.confidence], item.event_id)))


def build_root_cause_report(events: Iterable[CausalEvent], target_event_id: str) -> dict:
    graph = build_causal_graph(events)
    candidates = root_cause_candidates(graph, target_event_id)
    return {
        "schema": "isaac.causal_root_cause.v1",
        "target_event_id": target_event_id,
        "candidate_count": len(candidates),
        "candidates": [candidate.as_dict() for candidate in candidates],
        "verified": [candidate.as_dict() for candidate in candidates
                     if candidate.confidence == CausalConfidence.VERIFIED],
        "warning": (
            "Temporal adjacency is observational and must not be presented as proven causation."
        ),
    }
