"""
Memory API Routes.

Endpoints for insight storage and semantic search.
Delegates to RAG Service for insight queries and knowledge graph.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

from shared.config import get_settings
logger = get_logger(__name__)

router = APIRouter()

_HTTP_TIMEOUT = get_settings().timeouts.default


def _rag_url() -> str:
    return ServiceRegistry.get_url(ServiceName.RAG_SERVICE)


# ============================================================================
# Models
# ============================================================================


class SearchRequest(BaseModel):
    """Semantic search request."""

    query: str
    limit: int = Field(default_factory=lambda: get_settings().memory.search_limit, ge=1, le=get_settings().memory.search_max_limit)
    min_confidence: float = Field(default_factory=lambda: get_settings().memory.min_confidence, ge=0.0, le=1.0)
    domain: str | None = None


class InsightResponse(BaseModel):
    """Atomic insight response."""

    insight_id: str
    entity: str
    attribute: str
    value: str
    unit: str | None
    period: str | None
    origin_url: str
    confidence_score: float


# ============================================================================
# Routes
# ============================================================================


@router.post("/search")
async def search_insights(request: SearchRequest) -> dict:
    """Semantic search for atomic insights — delegates to RAG Service /insights/search."""
    logger.info(f"Searching insights via RAG: {request.query[:50]}")
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{_rag_url()}/insights/search",
                json={
                    "query": request.query,
                    "limit": request.limit,
                    "min_confidence": request.min_confidence,
                    "domain": request.domain,
                },
            )
            resp.raise_for_status()
            insights = resp.json()
        return {"query": request.query, "results": insights, "total": len(insights)}
    except httpx.HTTPError as exc:
        logger.warning(f"RAG search failed: {exc}")
        raise HTTPException(status_code=502, detail=f"RAG service unavailable: {exc}")


@router.get("/insights/{insight_id}")
async def get_insight(insight_id: str) -> dict:
    """Get a specific insight by ID from the RAG Service."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(f"{_rag_url()}/insights/{insight_id}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Insight not found")
        resp.raise_for_status()
        return resp.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"RAG service unavailable: {exc}")


@router.get("/graph")
async def get_provenance_graph(
    entity: str | None = None,
    depth: int = Query(default=get_settings().memory.graph_depth, ge=1, le=get_settings().memory.graph_max_depth),
) -> dict:
    """Get provenance graph — delegates to RAG Service /knowledge/search."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{_rag_url()}/knowledge/search",
                json={"query": entity or "", "limit": get_settings().memory.graph_limit},
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
    """List system sessions from system_jobs table."""
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        rows = await pool.fetch(
            f"""
            SELECT job_id, query, status, created_at, completed_at
            FROM system_jobs
            ORDER BY created_at DESC
            LIMIT {get_settings().memory.session_limit}
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
    """Get session details from system_jobs table."""
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        row = await pool.fetchrow("SELECT * FROM system_jobs WHERE job_id = $1", session_id)
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
