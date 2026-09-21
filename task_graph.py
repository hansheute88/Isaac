from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EdgeType(Enum):
    PARENT = "parent"
    CHILD = "child"
    DEPENDENCY = "dependency"
    EVIDENCE = "evidence"
    DECISION = "decision"
    OUTCOME = "outcome"
    LEARNED_FROM = "learned_from"


@dataclass
class TaskGraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "metadata": self.metadata,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraphEdge:
        raw_type = data.get("edge_type", "parent")
        try:
            e_type = EdgeType(raw_type)
        except ValueError:
            e_type = EdgeType.PARENT
        return cls(
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            edge_type=e_type,
            metadata=data.get("metadata") or {},
            ts=float(data.get("ts", time.time())),
        )


@dataclass
class TaskGraphNode:
    id: str
    node_type: str = "task"  # e.g., task, evidence, decision, outcome, learning
    label: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "label": self.label,
            "payload": self.payload,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraphNode:
        return cls(
            id=data.get("id", ""),
            node_type=data.get("node_type", "task"),
            label=data.get("label", ""),
            payload=data.get("payload") or {},
            created_at=float(data.get("created_at", time.time())),
        )


@dataclass
class TaskGraph:
    nodes: dict[str, TaskGraphNode] = field(default_factory=dict)
    edges: list[TaskGraphEdge] = field(default_factory=list)

    def add_node(
        self,
        node_id: str,
        node_type: str = "task",
        label: str = "",
        payload: dict[str, Any] | None = None,
    ) -> TaskGraphNode:
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if label:
                node.label = label
            if payload:
                node.payload.update(payload)
            return node
        node = TaskGraphNode(
            id=node_id,
            node_type=node_type,
            label=label or node_id,
            payload=dict(payload or {}),
            created_at=time.time(),
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType | str,
        metadata: dict[str, Any] | None = None,
    ) -> TaskGraphEdge:
        if isinstance(edge_type, str):
            try:
                e_type = EdgeType(edge_type)
            except ValueError:
                e_type = EdgeType.PARENT
        else:
            e_type = edge_type

        # Ensure source and target nodes exist in the graph
        if source_id not in self.nodes:
            self.add_node(source_id, label=source_id)
        if target_id not in self.nodes:
            self.add_node(target_id, label=target_id)

        edge = TaskGraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=e_type,
            metadata=dict(metadata or {}),
            ts=time.time(),
        )
        self.edges.append(edge)
        return edge

    def get_related_nodes(self, node_id: str, edge_type: EdgeType | str | None = None, direction: str = "outgoing") -> list[str]:
        target_type = EdgeType(edge_type) if isinstance(edge_type, str) else edge_type
        res = []
        for e in self.edges:
            if target_type and e.edge_type != target_type:
                continue
            if direction in ("outgoing", "both") and e.source_id == node_id:
                res.append(e.target_id)
            elif direction in ("incoming", "both") and e.target_id == node_id:
                res.append(e.source_id)
        return res

    def get_parents(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.PARENT, direction="outgoing")

    def get_children(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.CHILD, direction="outgoing")

    def get_dependencies(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.DEPENDENCY, direction="outgoing")

    def get_evidence(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.EVIDENCE, direction="outgoing")

    def get_decisions(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.DECISION, direction="outgoing")

    def get_outcomes(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.OUTCOME, direction="outgoing")

    def get_learned_from(self, node_id: str) -> list[str]:
        return self.get_related_nodes(node_id, EdgeType.LEARNED_FROM, direction="outgoing")

    def build_causal_chain(self, node_id: str) -> dict[str, Any]:
        """Returns a structured representation of all causal influences around a node."""
        if node_id not in self.nodes:
            return {}

        return {
            "node": self.nodes[node_id].to_dict(),
            "parents": [self.nodes[nid].to_dict() for nid in self.get_parents(node_id) if nid in self.nodes],
            "children": [self.nodes[nid].to_dict() for nid in self.get_children(node_id) if nid in self.nodes],
            "dependencies": [self.nodes[nid].to_dict() for nid in self.get_dependencies(node_id) if nid in self.nodes],
            "evidence": [self.nodes[nid].to_dict() for nid in self.get_evidence(node_id) if nid in self.nodes],
            "decisions": [self.nodes[nid].to_dict() for nid in self.get_decisions(node_id) if nid in self.nodes],
            "outcomes": [self.nodes[nid].to_dict() for nid in self.get_outcomes(node_id) if nid in self.nodes],
            "learned_from": [self.nodes[nid].to_dict() for nid in self.get_learned_from(node_id) if nid in self.nodes],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraph:
        graph = cls()
        nodes_raw = data.get("nodes") or {}
        for nid, ndata in nodes_raw.items():
            graph.nodes[nid] = TaskGraphNode.from_dict(ndata)
        edges_raw = data.get("edges") or []
        for edata in edges_raw:
            graph.edges.append(TaskGraphEdge.from_dict(edata))
        return graph
