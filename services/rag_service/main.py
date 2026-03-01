from __future__ import annotations

import asyncio
import os
import json
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from services.rag_service.core import (
    InsightStore,
    create_artifact_store,
    create_vector_store,
)
from services.rag_service.core.dataset_loader import DatasetLoader
from services.rag_service.core.knowledge_store import KnowledgeStore, create_knowledge_store
from shared.config import get_settings
from shared.logging.main import LogConfig, get_logger, setup_logging, RequestLoggingMiddleware
from shared.schemas import AtomicInsight

logger = get_logger(__name__)

# Global stores
insight_store: InsightStore | None = None
dataset_loader: DatasetLoader | None = None
artifact_store = None
knowledge_store: KnowledgeStore | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    global insight_store, artifact_store, dataset_loader, knowledge_store

    settings = get_settings()

    setup_logging(
        LogConfig(
            level=settings.logging.level,
            format=settings.logging.format,
            service_name="rag_service",
        )
    )

    logger.info("Starting RAG Service")

    # Initialize stores
    vector_store = create_vector_store()
    insight_store = InsightStore(vector_store)
    dataset_loader = DatasetLoader()
    artifact_store = create_artifact_store()

    # Initialize knowledge store (graceful fallback if DATABASE_URL not set)
    try:
        knowledge_store = create_knowledge_store()
        # Explicitly trigger initialization (table creation) on startup
        await knowledge_store._registry._get_pool()
        logger.info("Knowledge store initialized and table verified")

        # Auto-sync knowledge files from the knowledge/ library on startup.
        import asyncio
        asyncio.create_task(_sync_knowledge_job())
        logger.info("Knowledge auto-sync scheduled (background)")
    except Exception as e:
        logger.error(f"Knowledge store failed to start: {e}", exc_info=True)
        knowledge_store = None

    logger.info("RAG Service initialized")

    yield

    logger.info("RAG Service stopped")


settings = get_settings()

app = FastAPI(
    title=f"{settings.app.name} - RAG Service",
    description="External Knowledge Engine (Hugging Face Integration)",
    version=settings.app.version,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())


# ============================================================================
# Models
# ============================================================================


class AddInsightRequest(BaseModel):
    """Add insight request."""

    entity: str
    attribute: str
    value: str
    unit: str | None = None
    period: str | None = None
    origin_url: str
    origin_title: str = ""
    confidence_score: float = Field(default_factory=lambda: get_settings().rag.default_confidence, ge=0.0, le=1.0)
    dataset_id: str | None = None


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    limit: int = Field(
        default=settings.rag.default_limit, 
        ge=1, 
        le=settings.rag.max_limit, 
        description="Max results"
    )
    entity: str | None = None
    dataset_id: str | None = None
    min_confidence: float = Field(default_factory=lambda: get_settings().rag.min_confidence, ge=0.0, le=1.0)


class IngestRequest(BaseModel):
    """Dataset ingestion request."""

    dataset_name: str
    split: str = "train"
    max_rows: int = settings.rag.ingest_max_rows
    mapping: dict[str, str] | None = None


class InsightResponse(BaseModel):
    """Insight response."""

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


@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "healthy", "service": "rag_service", "timestamp": datetime.utcnow().isoformat()}


@app.post("/insights", response_model=dict)
async def add_insight(request: AddInsightRequest):
    """Add a new atomic insight."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    insight = AtomicInsight(
        insight_id="",
        entity=request.entity,
        attribute=request.attribute,
        value=request.value,
        unit=request.unit,
        period=request.period,
        origin_url=request.origin_url,
        origin_title=request.origin_title,
        confidence_score=request.confidence_score,
    )

    insight_id = await insight_store.add_insight(insight, dataset_id=request.dataset_id)
    return {"insight_id": insight_id}


@app.post("/insights/search", response_model=list[InsightResponse])
async def search_insights(request: SearchRequest):
    """Search for insights."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    insights = await insight_store.search(
        query=request.query,
        limit=request.limit,
        entity=request.entity,
        dataset_id=request.dataset_id,
        min_confidence=request.min_confidence,
    )

    return [
        InsightResponse(
            insight_id=i.insight_id,
            entity=i.entity,
            attribute=i.attribute,
            value=i.value,
            unit=i.unit,
            period=i.period,
            origin_url=i.origin_url,
            confidence_score=i.confidence_score,
        )
        for i in insights
    ]


@app.get("/insights/{insight_id}", response_model=InsightResponse)
async def get_insight(insight_id: str):
    """Get a specific insight."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    insight = await insight_store.get_insight(insight_id)
    if not insight:
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Insight not found"
        )

    return InsightResponse(
        insight_id=insight.insight_id,
        entity=insight.entity,
        attribute=insight.attribute,
        value=insight.value,
        unit=insight.unit,
        period=insight.period,
        origin_url=insight.origin_url,
        confidence_score=insight.confidence_score,
    )


@app.delete("/insights/{insight_id}")
async def delete_insight(insight_id: str):
    """Delete an insight."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    await insight_store.delete_insight(insight_id)
    return {"message": "Insight deleted"}


@app.get("/entities")
async def list_entities():
    """List all unique entities."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    entities = await insight_store.get_entities()
    return {"entities": entities}


# ============================================================================
# Dataset Routes
# ============================================================================


async def _ingest_job(request: IngestRequest):
    """Background task for ingestion."""
    if not dataset_loader or not insight_store:
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

            # Batch insert
            if len(facts_buffer) >= get_settings().rag.batch_size:
                await insight_store.add_insights(facts_buffer, dataset_id=request.dataset_name)
                count += len(facts_buffer)
                facts_buffer.clear()

        # Insert remaining
        if facts_buffer:
            await insight_store.add_insights(facts_buffer, dataset_id=request.dataset_name)
            count += len(facts_buffer)

        logger.info(f"Ingestion complete: {request.dataset_name} ({count} insights)")

    except Exception as e:
        logger.error(f"Ingestion failed for {request.dataset_name}: {e}")


@app.post("/datasets/ingest")
async def ingest_dataset(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger background ingestion of a generic HF dataset."""
    if not dataset_loader:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Dataset service not initialized"
        )

    background_tasks.add_task(_ingest_job, request)
    return {"message": "Ingestion started", "dataset": request.dataset_name}


@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Unload/Delete a dataset."""
    if not insight_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Insight store not initialized"
        )

    count = await insight_store.delete_by_dataset(dataset_id)
    return {"message": "Dataset deleted", "count": count}


# ============================================================================
# Knowledge Routes
# ============================================================================


class KnowledgeSearchRequest(BaseModel):
    """Knowledge search request."""

    query: str
    limit: int = Field(default=get_settings().api.default_limit, ge=1, le=get_settings().rag.max_limit)
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
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Knowledge store not initialized"
        )

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
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Knowledge store not initialized"
        )

    item = await knowledge_store.get_by_id(knowledge_id)
    if not item:
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Knowledge item not found"
        )

    return KnowledgeResponse(
        knowledge_id=item["knowledge_id"],
        name=item["name"],
        description=item["description"],
        domain=item["domain"],
        category=item["category"],
        tags=item.get("tags", []),
        content=item["content"],
    )


# Global lock to prevent concurrent knowledge sync jobs
_sync_lock = asyncio.Lock()

@app.post("/knowledge/sync")
async def sync_knowledge(background: bool = True):
    """
    Triggers a full synchronization of knowledge files from disk to the database.
    
    Args:
        background: If True, returns immediately. If False, waits for sync to finish.
    """
    if not knowledge_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Knowledge store not initialized"
        )

    if background:
        if _sync_lock.locked():
            return {"status": "sync_in_progress", "detail": "Background indexing already running"}
        asyncio.create_task(_sync_knowledge_job())
        return {"status": "sync_started", "detail": "Indexing in background"}
    else:
        # If running in foreground, wait for the lock (so we block until the job completes)
        async with _sync_lock:
            pass # Just to wait for it if it's already running
        
        # Then, we can't just run it again if we just waited, but wait, the job might have finished.
        # Actually, it's safer to just run it. The registry handles deduplication.
        await _sync_knowledge_job()
         
        count = 0
        if knowledge_store:
            count = await knowledge_store.count()
        return {"status": "sync_complete", "items_indexed": count}


async def _sync_knowledge_job(domain: str | None = None, category: str | None = None):
    """Background job to sync knowledge files from the library directory."""
    async with _sync_lock:
        logger.info("🚀 Starting Knowledge Library Sync...")
        try:
            from pathlib import Path
            from knowledge.index_knowledge import scan_knowledge_files
            
            settings = get_settings()
            
            # Resolve project root relative to this file
            # services/rag_service/main.py -> Kea/
            root_dir = Path(__file__).resolve().parents[2]
            knowledge_dir = root_dir / settings.app.knowledge_dir
            
            logger.info(f"Scanning directory: {knowledge_dir}")
            if not knowledge_dir.exists():
                logger.error(f"Knowledge directory does not exist: {knowledge_dir}")
                return

            items = scan_knowledge_files(knowledge_dir, domain_filter=domain, category_filter=category)
            
            logger.info(f"Sync: Found {len(items)} items to process in library.")

            if items and knowledge_store:
                try:
                    updated = await knowledge_store.sync(items)
                    logger.info(f"✅ Sync Complete: {updated} items updated in database.")
                except Exception as e:
                    logger.error(f"❌ Sync Failed during database update: {e}", exc_info=True)
            else:
                if not items:
                    logger.warning("Sync: No indexable items found in directory (check frontmatter 'name' fields).")
                if not knowledge_store:
                    logger.error("Sync: Knowledge store not initialized.")
        except Exception as e:
            logger.error(f"❌ Knowledge sync failed: {e}", exc_info=True)


@app.get("/knowledge/stats/summary")
async def knowledge_stats():
    """Get knowledge registry statistics."""
    if not knowledge_store:
        raise HTTPException(
            status_code=get_settings().status_codes.service_unavailable, 
            detail="Knowledge store not initialized"
        )

    count = await knowledge_store.count()
    return {
        "status": "online",
        "total_items": count,
        "syncing": _sync_lock.locked()
    }


# ============================================================================
# Main
# ============================================================================


def main():
    import uvicorn

    settings = get_settings()

    from shared.service_registry import ServiceRegistry, ServiceName
    uvicorn.run(
        "services.rag_service.main:app",
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.RAG_SERVICE),
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()
