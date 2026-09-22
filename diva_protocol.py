from __future__ import annotations

"""
Isaac – DIVA-Protokoll (Debug-/Herkunfts-Unsicherheits-Protokoll)
================================================================
Implementiert systemweite Behandlung von Herkunfts-Unsicherheit.

Kernprinzipien:
 - Auslösung nur bei unklarer/unvollständiger Provenance & Verhaltensrelevanz.
 - Zustandsbehaftete Auswirkung auf Priorisierung, Memory-Abruf, Modulatoren und Verhalten.
 - Kopplung mit Memory & In-Memory-Verbindungskarte (Synapsen-Graph).
 - Auditierbar, verfassungsgebunden und reversibel.
"""

import json
import logging
import time
import math
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import DATA_DIR, get_config
from state_io import atomic_write_json, load_json_or_recover
from memory import Memory, EpistemicClass, EpistemicMemoryEntry
from decision_trace import DecisionTrace, TracePhase
from audit import AuditLog

log = logging.getLogger("Isaac.DIVA")

DIVA_STATE_PATH = DATA_DIR / "diva_state.json"


class ProvenanceStatus(Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class ProvenanceChain:
    status: ProvenanceStatus = ProvenanceStatus.COMPLETE
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    derivation_steps: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "derivation_steps": list(self.derivation_steps),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProvenanceChain:
        if not data:
            return cls()
        raw_status = data.get("status", "complete")
        try:
            status = ProvenanceStatus(raw_status)
        except ValueError:
            status = ProvenanceStatus.COMPLETE
        return cls(
            status=status,
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp", time.time()),
            derivation_steps=list(data.get("derivation_steps", [])),
            confidence=float(data.get("confidence", 1.0)),
        )


@dataclass
class DIVAEvent:
    event_id: str = field(default_factory=lambda: f"diva_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    affected_info: str = ""
    uncertainty_score: float = 0.5  # 0.0 to 1.0
    behavioral_relevance: float = 0.5  # 0.0 to 1.0
    provenance: ProvenanceChain = field(default_factory=ProvenanceChain)
    resolved: bool = False
    resolution_reason: Optional[str] = None
    resolved_at: Optional[float] = None
    linked_memory_ids: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "affected_info": self.affected_info,
            "uncertainty_score": self.uncertainty_score,
            "behavioral_relevance": self.behavioral_relevance,
            "provenance": self.provenance.to_dict(),
            "resolved": self.resolved,
            "resolution_reason": self.resolution_reason,
            "resolved_at": self.resolved_at,
            "linked_memory_ids": list(self.linked_memory_ids),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DIVAEvent:
        prov_dict = data.get("provenance", {})
        prov = ProvenanceChain.from_dict(prov_dict)
        return cls(
            event_id=data.get("event_id", f"diva_{uuid.uuid4().hex[:8]}"),
            timestamp=data.get("timestamp", time.time()),
            affected_info=data.get("affected_info", ""),
            uncertainty_score=float(data.get("uncertainty_score", 0.5)),
            behavioral_relevance=float(data.get("behavioral_relevance", 0.5)),
            provenance=prov,
            resolved=bool(data.get("resolved", False)),
            resolution_reason=data.get("resolution_reason"),
            resolved_at=data.get("resolved_at"),
            linked_memory_ids=list(data.get("linked_memory_ids", [])),
            metadata=dict(data.get("metadata", {})),
        )


class ModulatorSystem:
    """
    Globale neuromodulatorische Schicht (hormonähnlich).
    Reguliert System-Verhalten bei DIVA-Aktivierung.
    """

    def __init__(
        self,
        uncertainty_arousal: float = 0.0,
        urgency_modifier: float = 0.0,
        memory_bias_strength: float = 0.0,
        decay_rate: float = 0.1,  # Decay rate per turn
    ):
        self.uncertainty_arousal = max(0.0, min(1.0, uncertainty_arousal))
        self.urgency_modifier = max(0.0, min(1.0, urgency_modifier))
        self.memory_bias_strength = max(0.0, min(1.0, memory_bias_strength))
        self.decay_rate = decay_rate

    def raise_for_diva(self, uncertainty_score: float, behavioral_relevance: float) -> None:
        impact = uncertainty_score * behavioral_relevance
        self.uncertainty_arousal = max(0.0, min(1.0, self.uncertainty_arousal + impact * 0.8))
        self.urgency_modifier = max(0.0, min(1.0, self.urgency_modifier + impact * 0.6))
        self.memory_bias_strength = max(0.0, min(1.0, self.memory_bias_strength + impact * 0.7))

    def decay(self, turns: int = 1, accelerated: bool = False) -> None:
        rate = self.decay_rate * (2.5 if accelerated else 1.0) * turns
        self.uncertainty_arousal = max(0.0, self.uncertainty_arousal - rate)
        self.urgency_modifier = max(0.0, self.urgency_modifier - rate)
        self.memory_bias_strength = max(0.0, self.memory_bias_strength - rate)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uncertainty_arousal": self.uncertainty_arousal,
            "urgency_modifier": self.urgency_modifier,
            "memory_bias_strength": self.memory_bias_strength,
            "decay_rate": self.decay_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModulatorSystem:
        return cls(
            uncertainty_arousal=float(data.get("uncertainty_arousal", 0.0)),
            urgency_modifier=float(data.get("urgency_modifier", 0.0)),
            memory_bias_strength=float(data.get("memory_bias_strength", 0.0)),
            decay_rate=float(data.get("decay_rate", 0.1)),
        )


class ConnectionMap:
    """
    Situations- / Synapsenkarte (Graph).
    Knoten: Situationen, Memory-Einträge, Goals, DIVA-Events.
    Kanten: Zeitliche, kausale oder Ähnlichkeitsbeziehungen mit Gewichten.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, Dict[str, float]] = {}  # "node_a->node_b": weight

    def add_node(self, node_id: str, node_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.nodes[node_id] = {
            "type": node_type,
            "data": data or {},
            "activated_at": time.time(),
        }

    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0, edge_type: str = "association") -> None:
        key = f"{source_id}->{target_id}"
        self.edges[key] = max(0.0, min(1.0, weight))

    def boost_connections(self, node_id: str, boost_factor: float = 0.3) -> None:
        for key in list(self.edges.keys()):
            src, tgt = key.split("->")
            if src == node_id or tgt == node_id:
                self.edges[key] = max(0.0, min(1.0, self.edges[key] + boost_factor))

    def get_associated_nodes(self, node_id: str, min_weight: float = 0.2) -> List[str]:
        neighbors = []
        for key, weight in self.edges.items():
            if weight < min_weight:
                continue
            src, tgt = key.split("->")
            if src == node_id:
                neighbors.append(tgt)
            elif tgt == node_id:
                neighbors.append(src)
        return list(set(neighbors))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConnectionMap:
        cm = cls()
        cm.nodes = dict(data.get("nodes", {}))
        cm.edges = {k: float(v) for k, v in data.get("edges", {}).items()}
        return cm


class DIVAProtocol:
    """
    Zentraler Manager für das DIVA-Protokoll.
    """

    def __init__(self, state_path: Path = DIVA_STATE_PATH, memory: Optional[Memory] = None):
        self.state_path = state_path
        self.memory = memory or Memory()
        self.enabled: bool = getattr(get_config(), "diva_enabled", True)
        self.relevance_threshold: float = getattr(get_config(), "diva_relevance_threshold", 0.4)
        self.modulators = ModulatorSystem()
        self.connection_map = ConnectionMap()
        self.active_events: Dict[str, DIVAEvent] = {}
        self.resolved_events: Dict[str, DIVAEvent] = {}
        self.total_triggered_count: int = 0
        self.total_resolved_count: int = 0
        self._load_state()

    def _load_state(self) -> None:
        data = load_json_or_recover(
            self.state_path,
            fallback_factory=lambda: {
                "modulators": {},
                "connection_map": {},
                "active_events": {},
                "resolved_events": {},
                "total_triggered_count": 0,
                "total_resolved_count": 0,
            },
            context="DIVA State",
        )
        if "modulators" in data:
            self.modulators = ModulatorSystem.from_dict(data["modulators"])
        if "connection_map" in data:
            self.connection_map = ConnectionMap.from_dict(data["connection_map"])
        if "active_events" in data:
            self.active_events = {
                k: DIVAEvent.from_dict(v) for k, v in data["active_events"].items()
            }
        if "resolved_events" in data:
            self.resolved_events = {
                k: DIVAEvent.from_dict(v) for k, v in data["resolved_events"].items()
            }
        self.total_triggered_count = int(data.get("total_triggered_count", 0))
        self.total_resolved_count = int(data.get("total_resolved_count", 0))

    def save_state(self) -> None:
        payload = {
            "modulators": self.modulators.to_dict(),
            "connection_map": self.connection_map.to_dict(),
            "active_events": {k: v.to_dict() for k, v in self.active_events.items()},
            "resolved_events": {k: v.to_dict() for k, v in self.resolved_events.items()},
            "total_triggered_count": self.total_triggered_count,
            "total_resolved_count": self.total_resolved_count,
        }
        atomic_write_json(self.state_path, payload)

    def evaluate_and_trigger(
        self,
        info: str,
        provenance: ProvenanceChain,
        behavioral_relevance: float,
        decision_trace: Optional[DecisionTrace] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DIVAEvent]:
        """
        Prüft Provenance und löst bei Unvollständigkeit & Verhaltensrelevanz ein DIVA-Event aus.
        """
        if not self.enabled:
            return None

        # Prüfen ob Provenance unvollständig (partial oder unknown)
        if provenance.status == ProvenanceStatus.COMPLETE:
            return None

        # Prüfen der Verhaltensrelevanz gegen Schwellenwert
        if behavioral_relevance < self.relevance_threshold:
            return None

        # Berechne Unsicherheits-Score
        uncertainty_score = 1.0 - provenance.confidence if provenance.confidence is not None else 0.8
        if provenance.status == ProvenanceStatus.UNKNOWN:
            uncertainty_score = max(uncertainty_score, 0.9)
        elif provenance.status == ProvenanceStatus.PARTIAL:
            uncertainty_score = max(uncertainty_score, 0.5)

        # Automatische Verknüpfung mit ähnlichen vergangenen Memories
        linked_ids = []
        try:
            facts = self.memory.search_facts(info, limit=5)
            for f in facts:
                if isinstance(f, dict) and "id" in f:
                    linked_ids.append(f["id"])
        except Exception as exc:
            log.warning("Memory search failed during DIVA trigger: %s", exc)

        event = DIVAEvent(
            affected_info=info,
            uncertainty_score=uncertainty_score,
            behavioral_relevance=behavioral_relevance,
            provenance=provenance,
            linked_memory_ids=linked_ids,
            metadata=metadata or {},
        )

        # Als EpistemicMemoryEntry (UNCERTAINTY_EVENT) speichern
        try:
            self.memory.add_epistemic_memory(
                key=f"diva:{event.event_id}",
                value=info,
                epistemic_class=EpistemicClass.UNCERTAINTY_EVENT,
                source=provenance.source,
                source_authority="diva_protocol",
                confidence=provenance.confidence,
                metadata={"event_dict": event.to_dict()},
            )
        except Exception as exc:
            log.warning("Failed to store DIVA epistemic memory entry: %s", exc)

        self.active_events[event.event_id] = event
        self.total_triggered_count += 1

        # Modulatoren anheben
        self.modulators.raise_for_diva(uncertainty_score, behavioral_relevance)

        # Verbindungskarte aktualisieren
        self.connection_map.add_node(event.event_id, "diva_event", event.to_dict())
        for mem_id in linked_ids:
            mem_node = f"memory_{mem_id}"
            self.connection_map.add_node(mem_node, "memory_entry", {"id": mem_id})
            self.connection_map.add_edge(event.event_id, mem_node, weight=0.7)
        self.connection_map.boost_connections(event.event_id, boost_factor=0.4)

        # Audit Log & DecisionTrace
        AuditLog.action("DIVAProtocol", "DIVA_EVENT_TRIGGERED", f"id={event.event_id} info={info[:30]}")
        if decision_trace is not None:
            decision_trace.add(
                phase=TracePhase.EVALUATION,
                event="diva_event_triggered",
                data=event.to_dict(),
            )

        log.info(
            "DIVA Event triggered: id=%s info='%s' uncertainty=%.2f arousal=%.2f linked_memories=%d",
            event.event_id,
            info[:40],
            uncertainty_score,
            self.modulators.uncertainty_arousal,
            len(linked_ids),
        )

        self.save_state()
        return event

    def resolve_event(
        self,
        event_id: str,
        reason: str,
        decision_trace: Optional[DecisionTrace] = None,
    ) -> bool:
        """
        Markiert ein DIVA-Event als resolved und beschleunigt den Modulator-Decay.
        """
        if event_id not in self.active_events:
            return False

        event = self.active_events.pop(event_id)
        event.resolved = True
        event.resolution_reason = reason
        event.resolved_at = time.time()
        self.resolved_events[event_id] = event
        self.total_resolved_count += 1

        # Beschleunigtes Abklingen
        self.modulators.decay(turns=1, accelerated=True)

        # Audit Log & DecisionTrace
        AuditLog.action("DIVAProtocol", "DIVA_EVENT_RESOLVED", f"id={event_id} reason={reason}")
        if decision_trace is not None:
            decision_trace.add(
                phase=TracePhase.EVALUATION,
                event="diva_event_resolved",
                data={"event_id": event_id, "reason": reason, "resolved_at": event.resolved_at},
            )

        log.info("DIVA Event resolved: id=%s reason='%s'", event_id, reason)
        self.save_state()
        return True

    def process_turn_decay(self) -> None:
        """Standardmäßiges Abklingen pro Turn."""
        if self.active_events:
            self.modulators.decay(turns=1, accelerated=False)
        else:
            # Schnelleres Abklingen wenn keine aktiven Events vorliegen
            self.modulators.decay(turns=1, accelerated=True)
        self.save_state()

    def get_metrics(self) -> Dict[str, Any]:
        """Gibt Metriken und Telemetriedaten des DIVA-Protokolls zurück."""
        active_durations = [time.time() - e.timestamp for e in self.active_events.values()]
        avg_active_duration = sum(active_durations) / len(active_durations) if active_durations else 0.0

        return {
            "active_events_count": len(self.active_events),
            "resolved_events_count": len(self.resolved_events),
            "total_triggered_count": self.total_triggered_count,
            "total_resolved_count": self.total_resolved_count,
            "modulator_values": self.modulators.to_dict(),
            "avg_active_duration_seconds": round(avg_active_duration, 2),
            "connection_map_nodes": len(self.connection_map.nodes),
            "connection_map_edges": len(self.connection_map.edges),
        }


_DIVA_INSTANCE: Optional[DIVAProtocol] = None


def get_diva_protocol() -> DIVAProtocol:
    global _DIVA_INSTANCE
    if _DIVA_INSTANCE is None:
        _DIVA_INSTANCE = DIVAProtocol()
    return _DIVA_INSTANCE



# ------------------------------------------------------------
# Modular Decay & Raising Helper Functions
# ------------------------------------------------------------

DEFAULT_HALF_LIVES: Dict[str, float] = {
    "uncertainty_arousal": 1800.0,   # 30 Minuten
    "urgency_modifier": 1200.0,      # 20 Minuten
    "memory_bias_strength": 2400.0,  # 40 Minuten
}

DEFAULT_BASE_RATES: Dict[str, float] = {
    "uncertainty_arousal": 0.08,
    "urgency_modifier": 0.10,
    "memory_bias_strength": 0.07,
}

DEFAULT_LOG_PARAMS: Dict[str, Dict[str, float]] = {
    "uncertainty_arousal": {"k": 0.35, "offset": 1.0},
    "urgency_modifier": {"k": 0.45, "offset": 1.0},
    "memory_bias_strength": {"k": 0.30, "offset": 1.0},
}

DEFAULT_LINEAR_TIMES: Dict[str, float] = {
    "uncertainty_arousal": 2400.0,   # 40 Minuten
    "urgency_modifier": 1800.0,      # 30 Minuten
    "memory_bias_strength": 3000.0,  # 50 Minuten
}

DEFAULT_RAISE_FACTORS: Dict[str, float] = {
    "uncertainty_arousal": 0.40,
    "urgency_modifier": 0.30,
    "memory_bias_strength": 0.35,
}

RESOLVED_HALF_LIFE_FACTOR: float = 0.25   # Halbwertszeit auf 25% reduzieren
RESOLVED_K_MULTIPLIER: float = 3.5        # k-Faktor für logarithmisches Decay
RESOLVED_BOOST_MULTIPLIER: float = 3.0    # Beschleunigung für Turn/Lineardecay


def create_initial_diva_modulators() -> Dict[str, Any]:
    return {
        "uncertainty_arousal": 0.0,
        "urgency_modifier": 0.0,
        "memory_bias_strength": 0.0,
        "last_update_ts": time.time(),
        "active_diva_events": [],
    }


def clamp_modulator(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def exponential_decay(
    current_value: float,
    elapsed_seconds: float,
    half_life_seconds: float,
) -> float:
    if current_value <= 0.0 or half_life_seconds <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    decayed = current_value * (0.5 ** (elapsed_seconds / half_life_seconds))
    return decayed if decayed > 1e-6 else 0.0


def logarithmic_decay(
    current_value: float,
    elapsed_seconds: float,
    k: float = 0.35,
    offset: float = 1.0,
) -> float:
    if current_value <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    log_term = math.log1p(elapsed_seconds)
    factor = 1.0 / (offset + k * log_term)
    decayed = current_value * factor
    return decayed if decayed > 1e-6 else 0.0


def linear_decay(
    current_value: float,
    elapsed_seconds: float,
    total_decay_seconds: float,
) -> float:
    if current_value <= 0.0 or total_decay_seconds <= 0.0:
        return 0.0
    if elapsed_seconds <= 0.0:
        return current_value

    progress = min(1.0, elapsed_seconds / total_decay_seconds)
    decayed = current_value * (1.0 - progress)
    return decayed if decayed > 1e-6 else 0.0


def turn_decay(
    current_value: float,
    rate: float,
    dt_turns: float = 1.0,
    factor: float = 1.0,
) -> float:
    if current_value <= 0.0:
        return 0.0

    decay_amount = rate * factor * dt_turns
    return max(0.0, current_value - decay_amount)


def raise_modulators(
    modulators: Dict[str, Any],
    uncertainty: float,
    relevance: float,
    event_id: Optional[str] = None,
    raise_factors: Optional[Dict[str, float]] = None,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    now_ts = now if now is not None else time.time()
    factors = raise_factors or DEFAULT_RAISE_FACTORS

    unc = clamp_modulator(uncertainty)
    rel = clamp_modulator(relevance)
    strength = min(1.0, unc * rel)

    for key, base_factor in factors.items():
        current = float(modulators.get(key, 0.0))
        delta = base_factor * strength
        modulators[key] = clamp_modulator(current + delta)

    modulators["last_update_ts"] = now_ts

    if event_id:
        active_events: List[str] = list(modulators.get("active_diva_events") or [])
        if event_id not in active_events:
            active_events.append(event_id)
        modulators["active_diva_events"] = active_events

    log.debug("DIVA modulators raised: strength=%.4f -> %s", strength, modulators)
    return modulators


def decay_modulators(
    modulators: Dict[str, Any],
    decay_type: str = "exponential",
    half_lives: Optional[Dict[str, float]] = None,
    base_rates: Optional[Dict[str, float]] = None,
    log_params: Optional[Dict[str, Dict[str, float]]] = None,
    linear_times: Optional[Dict[str, float]] = None,
    resolved: bool = False,
    dt_turns: float = 1.0,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    now_ts = now if now is not None else time.time()
    last_ts = float(modulators.get("last_update_ts") or now_ts)
    elapsed = max(0.0, now_ts - last_ts)

    keys = ("uncertainty_arousal", "urgency_modifier", "memory_bias_strength")
    decay_mode = (decay_type or "exponential").lower().strip()

    if decay_mode == "turn":
        rates = base_rates or DEFAULT_BASE_RATES
        boost_factor = RESOLVED_BOOST_MULTIPLIER if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            rate = float(rates.get(key, 0.08))
            modulators[key] = clamp_modulator(turn_decay(curr, rate, dt_turns=dt_turns, factor=boost_factor))
    elif decay_mode == "logarithmic":
        params_map = log_params or DEFAULT_LOG_PARAMS
        k_mult = RESOLVED_K_MULTIPLIER if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            p = params_map.get(key, {"k": 0.35, "offset": 1.0})
            k_val = float(p.get("k", 0.35)) * k_mult
            offset_val = float(p.get("offset", 1.0))
            modulators[key] = clamp_modulator(logarithmic_decay(curr, elapsed, k=k_val, offset=offset_val))
    elif decay_mode == "linear":
        times_map = linear_times or DEFAULT_LINEAR_TIMES
        factor = RESOLVED_HALF_LIFE_FACTOR if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            total_time = float(times_map.get(key, 2400.0)) * factor
            modulators[key] = clamp_modulator(linear_decay(curr, elapsed, total_time))
    else:  # exponential (default)
        hl_map = half_lives or DEFAULT_HALF_LIVES
        factor = RESOLVED_HALF_LIFE_FACTOR if resolved else 1.0
        for key in keys:
            curr = float(modulators.get(key, 0.0))
            hl = float(hl_map.get(key, 1800.0)) * factor
            modulators[key] = clamp_modulator(exponential_decay(curr, elapsed, hl))

    modulators["last_update_ts"] = now_ts
    return modulators


def on_diva_resolved(
    modulators: Dict[str, Any],
    event_id: Optional[str] = None,
    immediate_reduction_factor: float = 0.4,
    decay_type: str = "exponential",
    now: Optional[float] = None,
    **decay_kwargs: Any,
) -> Dict[str, Any]:
    now_ts = now if now is not None else time.time()

    if event_id:
        active_events: List[str] = list(modulators.get("active_diva_events") or [])
        if event_id in active_events:
            active_events.remove(event_id)
        modulators["active_diva_events"] = active_events

    for key in ("uncertainty_arousal", "urgency_modifier", "memory_bias_strength"):
        curr = float(modulators.get(key, 0.0))
        modulators[key] = clamp_modulator(curr * immediate_reduction_factor)

    return decay_modulators(
        modulators=modulators,
        decay_type=decay_type,
        resolved=True,
        now=now_ts,
        **decay_kwargs,
    )


def check_cognitive_loss_trigger(loss_delta_i: float, threshold: float = 2.0) -> bool:
    return loss_delta_i > threshold
