"""
RAG Service Main.

FastAPI service for fact storage and semantic search.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.rag_service.core import (
    FactStore,
    create_vector_store,
    create_artifact_store,
    Artifact,
)
from shared.schemas import AtomicFact
from shared.config import get_settings
from shared.logging import setup_logging, get_logger, LogConfig
from shared.logging.middleware import RequestLoggingMiddleware


logger = get_logger(__name__)

# Global stores
fact_store: FactStore | None = None
artifact_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global fact_store, artifact_store
    
    settings = get_settings()
    
    setup_logging(LogConfig(
        level=settings.log_level,
        format=settings.log_format,
        service_name="rag_service",
    ))
    
    logger.info("Starting RAG Service")
    
    # Initialize stores
    vector_store = create_vector_store()
    fact_store = FactStore(vector_store)
    artifact_store = create_artifact_store()
    
    logger.info("RAG Service initialized")
    
    yield
    
    logger.info("RAG Service stopped")


app = FastAPI(
    title="Kea RAG Service",
    description="Fact storage and semantic search service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)


# ============================================================================
# Models
# ============================================================================

class AddFactRequest(BaseModel):
    """Add fact request."""
    entity: str
    attribute: str
    value: str
    unit: str | None = None
    period: str | None = None
    source_url: str
    source_title: str = ""
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)


class SearchRequest(BaseModel):
    """Search request."""
    query: str
    limit: int = Field(default=10, ge=1, le=100)
    entity: str | None = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FactResponse(BaseModel):
    """Fact response."""
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag_service"}


@app.post("/facts", response_model=dict)
async def add_fact(request: AddFactRequest):
    """Add a new atomic fact."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")
    
    fact = AtomicFact(
        fact_id="",
        entity=request.entity,
        attribute=request.attribute,
        value=request.value,
        unit=request.unit,
        period=request.period,
        source_url=request.source_url,
        source_title=request.source_title,
        confidence_score=request.confidence_score,
    )
    
    fact_id = await fact_store.add_fact(fact)
    return {"fact_id": fact_id}


@app.post("/facts/search", response_model=list[FactResponse])
async def search_facts(request: SearchRequest):
    """Search for facts."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")
    
    facts = await fact_store.search(
        query=request.query,
        limit=request.limit,
        entity=request.entity,
        min_confidence=request.min_confidence,
    )
    
    return [
        FactResponse(
            fact_id=f.fact_id,
            entity=f.entity,
            attribute=f.attribute,
            value=f.value,
            unit=f.unit,
            period=f.period,
            source_url=f.source_url,
            confidence_score=f.confidence_score,
        )
        for f in facts
    ]


@app.get("/facts/{fact_id}", response_model=FactResponse)
async def get_fact(fact_id: str):
    """Get a specific fact."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")
    
    fact = await fact_store.get_fact(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    
    return FactResponse(
        fact_id=fact.fact_id,
        entity=fact.entity,
        attribute=fact.attribute,
        value=fact.value,
        unit=fact.unit,
        period=fact.period,
        source_url=fact.source_url,
        confidence_score=fact.confidence_score,
    )


@app.delete("/facts/{fact_id}")
async def delete_fact(fact_id: str):
    """Delete a fact."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")
    
    await fact_store.delete_fact(fact_id)
    return {"message": "Fact deleted"}


@app.get("/entities")
async def list_entities():
    """List all unique entities."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")
    
    entities = await fact_store.get_entities()
    return {"entities": entities}


# ============================================================================
# Main
# ============================================================================

def main():
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "services.rag_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()
