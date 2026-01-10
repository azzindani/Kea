"""
GraphRAG Layer.

Knowledge graph for fact relationships and provenance.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    type: str  # entity, fact, source, session
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    id: str
    source_id: str
    target_id: str
    relation: str  # has_fact, from_source, supports, contradicts
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


class GraphRAG:
    """
    In-memory knowledge graph for fact relationships.
    
    Features:
    - Entity-fact-source relationships
    - Provenance tracking
    - Contradiction detection
    - Path finding between entities
    
    Example:
        graph = GraphRAG()
        
        # Add entity
        entity_id = graph.add_entity("Indonesia Nickel Production", {"type": "commodity"})
        
        # Add fact connected to entity
        fact_id = graph.add_fact(entity_id, "volume", "1.5M tons", source_url="...")
        
        # Find related facts
        facts = graph.get_entity_facts(entity_id)
    """
    
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._entity_index: dict[str, str] = {}  # label -> node_id
        self._adjacency: dict[str, list[str]] = {}  # node_id -> [edge_ids]
    
    def add_entity(self, label: str, properties: dict | None = None) -> str:
        """Add or get an entity node."""
        # Check if exists
        if label in self._entity_index:
            return self._entity_index[label]
        
        node_id = f"entity-{uuid.uuid4().hex[:8]}"
        node = GraphNode(
            id=node_id,
            type="entity",
            label=label,
            properties=properties or {},
        )
        
        self._nodes[node_id] = node
        self._entity_index[label] = node_id
        self._adjacency[node_id] = []
        
        return node_id
    
    def add_fact(
        self,
        entity_id: str,
        attribute: str,
        value: str,
        source_url: str,
        confidence: float = 0.8,
    ) -> str:
        """Add a fact connected to an entity."""
        fact_id = f"fact-{uuid.uuid4().hex[:8]}"
        
        fact_node = GraphNode(
            id=fact_id,
            type="fact",
            label=f"{attribute}: {value}",
            properties={
                "attribute": attribute,
                "value": value,
                "confidence": confidence,
            },
        )
        
        self._nodes[fact_id] = fact_node
        self._adjacency[fact_id] = []
        
        # Connect entity -> fact
        edge_id = self._add_edge(entity_id, fact_id, "has_fact")
        
        # Add source if provided
        if source_url:
            source_id = self.add_source(source_url)
            self._add_edge(fact_id, source_id, "from_source")
        
        return fact_id
    
    def add_source(self, url: str, properties: dict | None = None) -> str:
        """Add a source node."""
        # Check if exists
        for node in self._nodes.values():
            if node.type == "source" and node.properties.get("url") == url:
                return node.id
        
        source_id = f"source-{uuid.uuid4().hex[:8]}"
        
        source_node = GraphNode(
            id=source_id,
            type="source",
            label=url,
            properties={"url": url, **(properties or {})},
        )
        
        self._nodes[source_id] = source_node
        self._adjacency[source_id] = []
        
        return source_id
    
    def add_relation(
        self,
        fact_id_1: str,
        fact_id_2: str,
        relation: str,  # supports, contradicts, related
        weight: float = 1.0,
    ) -> str:
        """Add a relation between facts."""
        return self._add_edge(fact_id_1, fact_id_2, relation, weight)
    
    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
    ) -> str:
        """Internal edge creation."""
        edge_id = f"edge-{uuid.uuid4().hex[:8]}"
        
        edge = GraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
        )
        
        self._edges[edge_id] = edge
        
        if source_id in self._adjacency:
            self._adjacency[source_id].append(edge_id)
        
        return edge_id
    
    def get_entity(self, entity_id: str) -> GraphNode | None:
        """Get an entity node."""
        node = self._nodes.get(entity_id)
        if node and node.type == "entity":
            return node
        return None
    
    def get_entity_by_label(self, label: str) -> GraphNode | None:
        """Get entity by label."""
        entity_id = self._entity_index.get(label)
        if entity_id:
            return self._nodes.get(entity_id)
        return None
    
    def get_entity_facts(self, entity_id: str) -> list[GraphNode]:
        """Get all facts for an entity."""
        facts = []
        
        for edge_id in self._adjacency.get(entity_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relation == "has_fact":
                fact_node = self._nodes.get(edge.target_id)
                if fact_node:
                    facts.append(fact_node)
        
        return facts
    
    def get_fact_sources(self, fact_id: str) -> list[GraphNode]:
        """Get all sources for a fact."""
        sources = []
        
        for edge_id in self._adjacency.get(fact_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relation == "from_source":
                source_node = self._nodes.get(edge.target_id)
                if source_node:
                    sources.append(source_node)
        
        return sources
    
    def find_contradictions(self, entity_id: str) -> list[tuple[GraphNode, GraphNode]]:
        """Find contradicting facts for an entity."""
        facts = self.get_entity_facts(entity_id)
        contradictions = []
        
        # Group facts by attribute
        by_attribute: dict[str, list[GraphNode]] = {}
        for fact in facts:
            attr = fact.properties.get("attribute", "")
            if attr not in by_attribute:
                by_attribute[attr] = []
            by_attribute[attr].append(fact)
        
        # Find different values for same attribute
        for attr, attr_facts in by_attribute.items():
            if len(attr_facts) > 1:
                values = set(f.properties.get("value") for f in attr_facts)
                if len(values) > 1:
                    # Multiple different values = potential contradiction
                    contradictions.append((attr_facts[0], attr_facts[1]))
        
        return contradictions
    
    def get_provenance_path(
        self,
        entity_id: str,
        max_depth: int = 3,
    ) -> dict:
        """Get provenance graph for an entity."""
        visited = set()
        nodes = []
        edges = []
        
        def traverse(node_id: str, depth: int):
            if depth > max_depth or node_id in visited:
                return
            
            visited.add(node_id)
            node = self._nodes.get(node_id)
            if node:
                nodes.append({
                    "id": node.id,
                    "type": node.type,
                    "label": node.label[:50],
                })
            
            for edge_id in self._adjacency.get(node_id, []):
                edge = self._edges.get(edge_id)
                if edge:
                    edges.append({
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "relation": edge.relation,
                    })
                    traverse(edge.target_id, depth + 1)
        
        traverse(entity_id, 0)
        
        return {"nodes": nodes, "edges": edges}
    
    def to_dict(self) -> dict:
        """Export graph as dictionary."""
        return {
            "nodes": [
                {"id": n.id, "type": n.type, "label": n.label, "properties": n.properties}
                for n in self._nodes.values()
            ],
            "edges": [
                {"id": e.id, "source": e.source_id, "target": e.target_id, "relation": e.relation}
                for e in self._edges.values()
            ],
        }
    
    def stats(self) -> dict:
        """Get graph statistics."""
        type_counts: dict[str, int] = {}
        for node in self._nodes.values():
            type_counts[node.type] = type_counts.get(node.type, 0) + 1
        
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "nodes_by_type": type_counts,
        }
