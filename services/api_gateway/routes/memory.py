"""
Memory API Routes.

Endpoints for fact storage and semantic search.
Delegates to RAG Service (port 8003) for fact queries and knowledge graph.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from shared.logging import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)

router = APIRouter()

_HTTP_TIMEOUT = 30.0


def _rag_url() -> str:
    return ServiceRegistry.get_url(ServiceName.RAG_SERVICE)


# ============================================================================
# Models
# ============================================================================


class SearchRequest(BaseModel):
    """Semantic search request."""

    query: str
    limit: int = Field(default=10, ge=1, le=100)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    domain: str | None = None


class FactResponse(BaseModel):
    """Atomic fact response."""

    fact_id: str
    entity: str
    attribute: str
    value: str
    unit: str | None
    period: str | None
    source_url: str
    confidence_score: float


# ============================================================================
# Routes
# ============================================================================


@router.post("/search")
async def search_facts(request: SearchRequest) -> dict:
    """Semantic search for atomic facts — delegates to RAG Service /facts/search."""
    logger.info(f"Searching facts via RAG: {request.query[:50]}")
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{_rag_url()}/facts/search",
                json={
                    "query": request.query,
                    "limit": request.limit,
                    "min_confidence": request.min_confidence,
                    "domain": request.domain,
                },
            )
            resp.raise_for_status()
            facts = resp.json()
        return {"query": request.query, "results": facts, "total": len(facts)}
    except httpx.HTTPError as exc:
        logger.warning(f"RAG search failed: {exc}")
        raise HTTPException(status_code=502, detail=f"RAG service unavailable: {exc}")


@router.get("/facts/{fact_id}")
async def get_fact(fact_id: str) -> dict:
    """Get a specific fact by ID from the RAG Service."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(f"{_rag_url()}/facts/{fact_id}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Fact not found")
        resp.raise_for_status()
        return resp.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"RAG service unavailable: {exc}")


@router.get("/graph")
async def get_provenance_graph(
    entity: str | None = None,
    depth: int = Query(default=2, ge=1, le=5),
) -> dict:
    """Get provenance graph — delegates to RAG Service /knowledge/search."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{_rag_url()}/knowledge/search",
                json={"query": entity or "", "limit": 50},
            )
            resp.raise_for_status()
            items = resp.json()
        # Convert flat knowledge list to a minimal nodes/edges graph
        nodes = [
            {
                "id": k.get("knowledge_id", ""),
                "label": k.get("name", ""),
                "domain": k.get("domain", ""),
            }
            for k in items
        ]
        return {"nodes": nodes, "edges": [], "entity": entity, "depth": depth}
    except httpx.HTTPError as exc:
        logger.warning(f"RAG knowledge search failed: {exc}")
        return {"nodes": [], "edges": [], "entity": entity, "depth": depth}


@router.get("/sessions")
async def list_sessions() -> dict:
    """List research sessions from research_jobs table."""
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        rows = await pool.fetch(
            """
            SELECT job_id, query, status, created_at, completed_at
            FROM research_jobs
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        sessions = [
            {
                "session_id": r["job_id"],
                "query": r["query"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
            }
            for r in rows
        ]
        return {"sessions": sessions}
    except Exception as exc:
        logger.warning(f"Session list failed: {exc}")
        return {"sessions": []}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get session details from research_jobs table."""
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        row = await pool.fetchrow("SELECT * FROM research_jobs WHERE job_id = $1", session_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        r = dict(row)
        for k in ("created_at", "completed_at", "updated_at"):
            if r.get(k):
                r[k] = r[k].isoformat()
        return r
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Session fetch failed: {exc}")
        raise HTTPException(status_code=404, detail="Session not found")
