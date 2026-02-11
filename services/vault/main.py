"""
Vault Service — Research Persistence & Context Engine (Port 8004).

Routes:
  GET    /health
  POST   /audit/logs
  GET    /audit/logs
  POST   /checkpoints                  Save a LangGraph state snapshot
  GET    /checkpoints/{job_id}         Load latest checkpoint for a job
  GET    /checkpoints/{job_id}/list    List checkpoint node names for a job
  DELETE /checkpoints/{job_id}         Delete all checkpoints for a job
  POST   /contexts                     Store an arbitrary context blob
  GET    /contexts/{context_id}        Retrieve a stored context blob
  POST   /search                       Text search over stored checkpoints
"""

from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.vault.core.audit_trail import AuditEventType, get_audit_trail
from services.vault.core.checkpointing import get_checkpoint_store
from shared.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="The Vault")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "vault"}


# ============================================================================
# Audit routes
# ============================================================================


class LogEventRequest(BaseModel):
    event_type: str
    action: str
    actor: str = "system"
    resource: str = ""
    details: dict[str, Any] = {}
    session_id: str = ""


@app.post("/audit/logs")
async def log_event(request: LogEventRequest) -> dict:
    """Log an audit event."""
    audit = get_audit_trail()
    try:
        event_type = AuditEventType(request.event_type)
    except ValueError:
        try:
            event_type = AuditEventType(request.event_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

    entry_id = await audit.log(
        event_type=event_type,
        action=request.action,
        actor=request.actor,
        resource=request.resource,
        details=request.details,
        session_id=request.session_id,
    )
    return {"entry_id": entry_id}


@app.get("/audit/logs")
async def search_logs(
    limit: int = 100,
    actor: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Search audit logs."""
    audit = get_audit_trail()
    entries = await audit.query(limit=limit, actor=actor, session_id=session_id)
    return {"entries": [e.to_dict() for e in entries]}


# ============================================================================
# Checkpoint routes
# ============================================================================


class SaveCheckpointRequest(BaseModel):
    job_id: str
    node_name: str
    state: dict[str, Any]


@app.post("/checkpoints", status_code=201)
async def save_checkpoint(request: SaveCheckpointRequest) -> dict:
    """Save a LangGraph state snapshot."""
    store = await get_checkpoint_store()
    await store.save(request.job_id, request.node_name, request.state)
    return {"job_id": request.job_id, "node_name": request.node_name, "saved": True}


@app.get("/checkpoints/{job_id}")
async def load_checkpoint(job_id: str) -> dict:
    """Load the most recent checkpoint for a job."""
    store = await get_checkpoint_store()
    result = await store.load_latest(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No checkpoint found for this job")
    node_name, state = result
    return {"job_id": job_id, "node_name": node_name, "state": state}


@app.get("/checkpoints/{job_id}/list")
async def list_job_checkpoints(job_id: str) -> dict:
    """List all checkpoint node names saved for a job."""
    store = await get_checkpoint_store()
    checkpoints = await store.list_checkpoints(job_id)
    return {"job_id": job_id, "checkpoints": checkpoints}


@app.delete("/checkpoints/{job_id}", status_code=200)
async def delete_job_checkpoints(job_id: str) -> dict:
    """Delete all checkpoints for a job (post-completion cleanup)."""
    store = await get_checkpoint_store()
    deleted = await store.delete_job_checkpoints(job_id)
    return {"job_id": job_id, "deleted_count": deleted}


# ============================================================================
# Context (key-value blob) routes — reuse CheckpointStore with node="_context"
# ============================================================================

_CONTEXT_NODE = "_context"


class ContextUpsertRequest(BaseModel):
    context_id: str
    data: dict[str, Any] = Field(default_factory=dict)


@app.post("/contexts", status_code=201)
async def upsert_context(request: ContextUpsertRequest) -> dict:
    """Store or update an arbitrary context blob."""
    store = await get_checkpoint_store()
    await store.save(request.context_id, _CONTEXT_NODE, request.data)
    return {"context_id": request.context_id, "saved": True}


@app.get("/contexts/{context_id}")
async def get_context(context_id: str) -> dict:
    """Retrieve a stored context blob by ID."""
    store = await get_checkpoint_store()
    data = await store.load(context_id, _CONTEXT_NODE)
    if data is None:
        raise HTTPException(status_code=404, detail="Context not found")
    return {"context_id": context_id, "data": data}


# ============================================================================
# Search route — full-text search over stored checkpoints / contexts
# ============================================================================


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=200)


@app.post("/search")
async def search_vault(request: SearchRequest) -> dict:
    """
    Text search over stored checkpoints and contexts.

    Performs a case-insensitive ILIKE scan on the serialised state column in
    graph_checkpoints, returning (job_id, node_name, created_at) triples.
    """
    store = await get_checkpoint_store()
    if store._pool is None:
        return {"query": request.query, "results": [], "total": 0}

    try:
        async with store._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT job_id, node_name, created_at
                FROM graph_checkpoints
                WHERE state::text ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                f"%{request.query}%",
                request.limit,
            )
        results = [
            {
                "job_id": r["job_id"],
                "node_name": r["node_name"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]
        return {"query": request.query, "results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Vault search failed: {e}")
        return {"query": request.query, "results": [], "total": 0}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
