"""
Provenance Graph API Routes.

Endpoints for fact provenance and knowledge graph.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


# In-memory graph (use GraphRAG in production)
_entities: dict[str, dict] = {}
_facts: dict[str, dict] = {}
_edges: list[dict] = []


# ============================================================================
# Models
# ============================================================================

class EntityNode(BaseModel):
    """Entity in the knowledge graph."""
    id: str
    label: str
    type: str = "entity"
    properties: dict = {}


class FactNode(BaseModel):
    """Fact in the knowledge graph."""
    id: str
    attribute: str
    value: str
    confidence: float
    source_url: str


class GraphEdge(BaseModel):
    """Edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation: str


# ============================================================================
# Routes
# ============================================================================

@router.get("/entities")
async def list_entities():
    """List all entities in the graph."""
    return {"entities": list(_entities.values())}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity with its facts."""
    if entity_id not in _entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = _entities[entity_id]
    
    # Get connected facts
    entity_facts = [
        f for f in _facts.values()
        if f.get("entity_id") == entity_id
    ]
    
    return {
        "entity": entity,
        "facts": entity_facts,
    }


@router.get("/entities/{entity_id}/provenance")
async def get_entity_provenance(entity_id: str, depth: int = 2):
    """Get provenance graph for an entity."""
    if entity_id not in _entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Build subgraph
    nodes = [_entities[entity_id]]
    edges = []
    
    # Add connected facts
    for fact in _facts.values():
        if fact.get("entity_id") == entity_id:
            nodes.append(fact)
            edges.append({
                "source_id": entity_id,
                "target_id": fact["id"],
                "relation": "has_fact",
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "entity_id": entity_id,
        "depth": depth,
    }


@router.get("/facts/{fact_id}")
async def get_fact(fact_id: str):
    """Get fact details."""
    if fact_id not in _facts:
        raise HTTPException(status_code=404, detail="Fact not found")
    
    return _facts[fact_id]


@router.get("/contradictions")
async def find_contradictions(entity_id: str | None = None):
    """Find contradicting facts."""
    # Group facts by entity and attribute
    by_entity_attr: dict[str, list[dict]] = {}
    
    for fact in _facts.values():
        if entity_id and fact.get("entity_id") != entity_id:
            continue
        
        key = f"{fact.get('entity_id')}:{fact.get('attribute')}"
        if key not in by_entity_attr:
            by_entity_attr[key] = []
        by_entity_attr[key].append(fact)
    
    # Find contradictions (different values for same attribute)
    contradictions = []
    
    for key, facts in by_entity_attr.items():
        if len(facts) > 1:
            values = set(f.get("value") for f in facts)
            if len(values) > 1:
                contradictions.append({
                    "attribute": facts[0].get("attribute"),
                    "facts": facts,
                })
    
    return {"contradictions": contradictions}


@router.get("/stats")
async def graph_stats():
    """Get graph statistics."""
    return {
        "total_entities": len(_entities),
        "total_facts": len(_facts),
        "total_edges": len(_edges),
    }
