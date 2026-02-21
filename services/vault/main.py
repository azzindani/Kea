"""
Vault Service — Persistence & Context Engine.

Routes:
  GET    /health
  POST   /audit/logs
  GET    /audit/logs
  POST   /audit/logs
  GET    /audit/logs
  POST   /persistence/sessions
  GET    /persistence/query
"""

from __future__ import annotations

from typing import Any

import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from services.vault.core.audit_trail import AuditEventType, get_audit_trail
from services.vault.core.postgres_store import PostgresVectorStore
from services.vault.core.vector_store import Document
from shared.logging.main import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
import os

# Initialize structured logging globally
# (Moved below settings loading)

logger = get_logger(__name__)

from shared.config import get_settings

# Load settings
settings = get_settings()

setup_logging(LogConfig(
    level=settings.logging.level,
    service_name="vault",
))

app = FastAPI(
    title=f"{settings.app.name} - Vault",
    description="System Persistence & Context Engine",
    version=settings.app.version,
)
app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())

# Global Vector Store
_vector_store: PostgresVectorStore | None = None


async def get_vector_store() -> PostgresVectorStore:
    """Lazy initialize and return the PostgresVectorStore."""
    global _vector_store
    if _vector_store is None:
        _vector_store = PostgresVectorStore()
    return _vector_store


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
    limit: int = settings.api.default_limit,
    actor: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Search audit logs."""
    audit = get_audit_trail()
    entries = await audit.query(limit=limit, actor=actor, session_id=session_id)
    return {"entries": [e.to_dict() for e in entries]}


# ============================================================================
# Persistence Routes — Semantic search over insights
# ============================================================================


class SaveSessionRequest(BaseModel):
    query: str
    job_id: str = ""
    content: str = ""
    confidence: float = 0.0
    facts: list[dict[str, Any]] = []


@app.post("/persistence/sessions", status_code=201)
async def save_execution_session(request: SaveSessionRequest) -> dict:
    """Persist execution results to the vector store for later retrieval."""
    store = await get_vector_store()

    # Create a document for the main content
    doc_id = f"session_{request.job_id or str(uuid.uuid4())[:8]}"
    doc = Document(
        id=doc_id,
        content=request.content,
        metadata={
            "query": request.query,
            "job_id": request.job_id,
            "confidence": request.confidence,
            "type": "execution_summary",
        },
    )

    # Also extract individual insights as documents for more granular retrieval
    documents = [doc]
    for i, insight in enumerate(request.facts):
        documents.append(
            Document(
                id=f"{doc_id}_insight_{i}",
                content=insight.get("text", ""),
                metadata={
                    "query": request.query,
                    "job_id": request.job_id,
                    "confidence": insight.get("confidence", 0.0),
                    "type": "atomic_insight",
                },
            )
        )

    await store.add(documents)
    return {"status": "saved", "document_id": doc_id, "insights_count": len(request.facts)}


@app.get("/persistence/query")
async def query_persistence(
    q: str,
    limit: int | None = None,
    domain: str | None = None,
) -> dict:
    """Semantic search over stored insights."""
    limit = limit or settings.vault_settings.default_limit
    store = await get_vector_store()

    filters = {}
    if domain:
        filters["domain"] = domain

    # Search for relevant facts or reports
    results = await store.search(
        query=q,
        limit=limit,
        filter=filters if filters else None,
    )

    # Format for generic system response
    facts = []
    for res in results:
        facts.append(
            {
                "text": res.content,
                "confidence": res.score,
                "metadata": res.metadata,
            }
        )

    return {"query": q, "facts": facts, "total": len(facts)}


if __name__ == "__main__":
    from shared.service_registry import ServiceRegistry, ServiceName
    uvicorn.run(
        app, 
        host=settings.api.host, 
        port=ServiceRegistry.get_port(ServiceName.VAULT)
    )
