"""
RAG Service Main.

FastAPI service for fact storage and semantic search.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.rag_service.core import (
    FactStore,
    create_artifact_store,
    create_vector_store,
)
from services.rag_service.core.dataset_loader import DatasetLoader
from services.rag_service.core.knowledge_store import KnowledgeStore, create_knowledge_store
from shared.config import get_settings
from shared.logging import LogConfig, get_logger, setup_logging, RequestLoggingMiddleware
from shared.schemas import AtomicFact

logger = get_logger(__name__)

# Global stores
fact_store: FactStore | None = None
dataset_loader: DatasetLoader | None = None
artifact_store = None
knowledge_store: KnowledgeStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global fact_store, artifact_store, dataset_loader, knowledge_store

    settings = get_settings()

    setup_logging(
        LogConfig(
            level=settings.log_level,
            format=settings.log_format,
            service_name="rag_service",
        )
    )

    logger.info("Starting RAG Service")

    # Initialize stores
    vector_store = create_vector_store()
    fact_store = FactStore(vector_store)
    dataset_loader = DatasetLoader()
    artifact_store = create_artifact_store()

    # Initialize knowledge store (graceful fallback if DATABASE_URL not set)
    try:
        knowledge_store = create_knowledge_store()
        logger.info("Knowledge store initialized")

        # Auto-sync knowledge files from the knowledge/ library on startup.
        # This ensures domain expertise (skills, rules, procedures) is always
        # available for retrieval without a manual POST /knowledge/sync call.
        import asyncio

        asyncio.create_task(_sync_knowledge_job())
        logger.info("Knowledge auto-sync scheduled (background)")
    except Exception as e:
        logger.warning(f"Knowledge store unavailable: {e}")
        knowledge_store = None

    logger.info("RAG Service initialized")

    yield

    logger.info("RAG Service stopped")


app = FastAPI(
    title="Project RAG Service",
    description="External Knowledge Engine (Hugging Face Integration)",
    version="0.2.0",
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
    dataset_id: str | None = None


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    limit: int = Field(
        default=10, ge=1, le=10000, description="Max results (up to 10000 for large-scale searches)"
    )
    entity: str | None = None
    dataset_id: str | None = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class IngestRequest(BaseModel):
    """Dataset ingestion request."""

    dataset_name: str
    split: str = "train"
    max_rows: int = 1000
    mapping: dict[str, str] | None = None


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

    fact_id = await fact_store.add_fact(fact, dataset_id=request.dataset_id)
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
        dataset_id=request.dataset_id,
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
# Dataset Routes
# ============================================================================


async def _ingest_job(request: IngestRequest):
    """Background task for ingestion."""
    if not dataset_loader or not fact_store:
        logger.error("Stores not initialized for background job")
        return

    try:
        logger.info(f"Starting ingestion: {request.dataset_name}")
        facts_buffer = []
        count = 0

        async for fact in dataset_loader.stream_dataset(
            dataset_name=request.dataset_name,
            split=request.split,
            max_rows=request.max_rows,
            mapping=request.mapping,
        ):
            facts_buffer.append(fact)

            # Batch insert every 50
            if len(facts_buffer) >= 50:
                await fact_store.add_facts(facts_buffer, dataset_id=request.dataset_name)
                count += len(facts_buffer)
                facts_buffer.clear()

        # Insert remaining
        if facts_buffer:
            await fact_store.add_facts(facts_buffer, dataset_id=request.dataset_name)
            count += len(facts_buffer)

        logger.info(f"Ingestion complete: {request.dataset_name} ({count} facts)")

    except Exception as e:
        logger.error(f"Ingestion failed for {request.dataset_name}: {e}")


@app.post("/datasets/ingest")
async def ingest_dataset(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger background ingestion of a generic HF dataset."""
    if not dataset_loader:
        raise HTTPException(status_code=503, detail="Dataset service not initialized")

    background_tasks.add_task(_ingest_job, request)
    return {"message": "Ingestion started", "dataset": request.dataset_name}


@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Unload/Delete a dataset."""
    if not fact_store:
        raise HTTPException(status_code=503, detail="Fact store not initialized")

    count = await fact_store.delete_by_dataset(dataset_id)
    return {"message": "Dataset deleted", "count": count}


# ============================================================================
# Knowledge Routes
# ============================================================================


class KnowledgeSearchRequest(BaseModel):
    """Knowledge search request."""

    query: str
    limit: int = Field(default=5, ge=1, le=20)
    domain: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    enable_reranking: bool = True


class KnowledgeResponse(BaseModel):
    """Knowledge item response."""

    knowledge_id: str
    name: str
    description: str
    domain: str
    category: str
    tags: list[str]
    content: str
    similarity: float = 0.0


class KnowledgeSyncRequest(BaseModel):
    """Knowledge sync request."""

    domain: str | None = None
    category: str | None = None


@app.post("/knowledge/search", response_model=list[KnowledgeResponse])
async def search_knowledge(request: KnowledgeSearchRequest):
    """Semantic search for knowledge items (skills, rules, personas)."""
    if not knowledge_store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized")

    results = await knowledge_store.search(
        query=request.query,
        limit=request.limit,
        domain=request.domain,
        category=request.category,
        tags=request.tags,
        enable_reranking=request.enable_reranking,
    )

    return [
        KnowledgeResponse(
            knowledge_id=r["knowledge_id"],
            name=r["name"],
            description=r["description"],
            domain=r["domain"],
            category=r["category"],
            tags=r.get("tags", []),
            content=r["content"],
            similarity=r.get("similarity", 0.0),
        )
        for r in results
    ]


@app.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    """Get a specific knowledge item by ID."""
    if not knowledge_store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized")

    item = await knowledge_store.get_by_id(knowledge_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    return KnowledgeResponse(
        knowledge_id=item["knowledge_id"],
        name=item["name"],
        description=item["description"],
        domain=item["domain"],
        category=item["category"],
        tags=item.get("tags", []),
        content=item["content"],
    )


@app.post("/knowledge/sync")
async def sync_knowledge(
    request: KnowledgeSyncRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger background indexing of knowledge files from the knowledge/ directory."""
    if not knowledge_store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized")

    background_tasks.add_task(_sync_knowledge_job, request.domain, request.category)
    return {"message": "Knowledge sync started"}


async def _sync_knowledge_job(
    domain: str | None = None,
    category: str | None = None,
) -> None:
    """Background job to index knowledge files."""
    try:
        from pathlib import Path

        from knowledge.index_knowledge import scan_knowledge_files

        knowledge_dir = Path(__file__).resolve().parents[2] / "knowledge"
        items = scan_knowledge_files(knowledge_dir, domain_filter=domain, category_filter=category)

        if items and knowledge_store:
            updated = await knowledge_store.sync(items)
            logger.info(f"Knowledge sync complete: {updated} items updated")
    except Exception as e:
        logger.error(f"Knowledge sync failed: {e}")


@app.get("/knowledge/stats/summary")
async def knowledge_stats():
    """Get knowledge registry statistics."""
    if not knowledge_store:
        raise HTTPException(status_code=503, detail="Knowledge store not initialized")

    count = await knowledge_store.count()
    return {"total_items": count}


# ============================================================================
# Main
# ============================================================================


def main():
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "services.rag_service.main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()
