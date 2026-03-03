"""
ML Inference Service — Main Entrypoint.

FastAPI application that serves embedding and reranking models
behind HTTP APIs. Configurable via ML_ROLE environment variable
to load only the required model(s).

Routes are conditionally mounted based on the configured role:
  - ML_ROLE=embedding → /v1/embed, /v1/embed/query
  - ML_ROLE=reranker  → /v1/rerank
  - ML_ROLE=both      → all endpoints
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from shared.config import get_settings
from shared.logging.main import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
from shared.service_registry import ServiceName, ServiceRegistry

from services.ml_inference.core.model_pool import ModelPool, ModelRole, get_model_pool
from services.ml_inference.core.schemas import (
    EmbedRequest,
    EmbedQueryRequest,
    EmbedResponse,
    EmbedQueryResponse,
    RerankRequest,
    RerankResponse,
    RerankResult,
    ModelsResponse,
    ModelInfo,
    HealthResponse,
)


# Load settings
settings = get_settings()

# Initialize structured logging
setup_logging(LogConfig(
    level=settings.logging.level,
    service_name="ml_inference",
))

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load models on startup, release on shutdown."""
    pool = get_model_pool()

    logger.info(
        f"ML Inference starting: role={pool.role.value}, "
        f"device_config={settings.ml_inference.device}"
    )

    try:
        await pool.load_models()
        logger.info(
            f"ML Inference ready: {pool.loaded_model_count} model(s) loaded "
            f"on {pool.device}"
        )
    except Exception as e:
        logger.error(f"Failed to load models during startup: {e}")
        # Service starts in degraded mode — /health will report the issue

    # Log registered routes for debugging
    for route in _app.routes:
        if hasattr(route, "path"):
            logger.debug(f"Registered route: {route.path}")

    yield

    logger.info("ML Inference shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


app = FastAPI(
    title=f"{settings.app.name} - ML Inference",
    description="Dedicated ML model serving for embedding and reranking",
    version=settings.app.version,
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())


# ---------------------------------------------------------------------------
# Health & Info Routes (always available)
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check with model and device status."""
    pool = get_model_pool()

    status = "ok" if pool.is_loaded and pool.loaded_model_count > 0 else "degraded"

    return HealthResponse(
        status=status,
        service="ml_inference",
        role=pool.role.value,
        models_loaded=pool.loaded_model_count,
        device=pool.device or "unknown",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List loaded models and their status."""
    pool = get_model_pool()
    models: list[ModelInfo] = []

    if pool.has_embedding:
        models.append(ModelInfo(
            name=settings.embedding.model_name,
            role="embedding",
            device=pool.device,
            loaded=True,
            dimension=settings.embedding.dimension,
        ))

    if pool.has_reranker:
        models.append(ModelInfo(
            name=settings.reranker.model_name,
            role="reranker",
            device=pool.device,
            loaded=True,
        ))

    if pool.has_vl_embedding:
        models.append(ModelInfo(
            name=settings.vl_embedding.model_name,
            role="vl_embedding",
            device=pool.device,
            loaded=True,
            dimension=settings.vl_embedding.dimension,
        ))

    if pool.has_vl_reranker:
        models.append(ModelInfo(
            name=settings.vl_reranker.model_name,
            role="vl_reranker",
            device=pool.device,
            loaded=True,
        ))

    return ModelsResponse(
        models=models,
        service_role=pool.role.value,
    )


@app.exception_handler(404)
async def custom_404_handler(request: Request, _exc: Exception):
    """Custom 404 handler to help debug missing routes."""
    logger.warning(f"404 Not Found: {request.method} {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={
            "detail": "ML Inference endpoint not found",
            "method": request.method,
            "path": request.url.path,
            "suggestion": "Check ServiceRegistry port and prefix (expected: /v1/embed, /v1/rerank)",
        },
    )


# ---------------------------------------------------------------------------
# Embedding Routes
# ---------------------------------------------------------------------------


@app.post("/v1/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """
    Batch text embedding.

    Accepts a list of texts and returns their embedding vectors.
    Optionally accepts an instruction to prepend to each text.
    """
    pool = get_model_pool()

    if not pool.has_embedding:
        raise HTTPException(
            status_code=settings.status_codes.service_unavailable,
            detail=f"Embedding model not available. Service role: {pool.role.value}",
        )

    # Enforce max batch size
    max_batch = settings.ml_inference.max_batch_size
    if len(request.texts) > max_batch:
        raise HTTPException(
            status_code=settings.status_codes.bad_request,
            detail=f"Batch size {len(request.texts)} exceeds maximum {max_batch}",
        )

    try:
        provider = pool.get_embedding_provider()
        embeddings = await provider.embed(request.texts)

        return EmbedResponse(
            embeddings=[list(e) for e in embeddings],
            model=settings.embedding.model_name,
            dimension=settings.embedding.dimension,
            count=len(embeddings),
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=settings.status_codes.internal_error,
            detail=f"Embedding inference failed: {e}",
        )


@app.post("/v1/embed/query", response_model=EmbedQueryResponse)
async def embed_query(request: EmbedQueryRequest):
    """
    Single query embedding (convenience endpoint).

    Embeds a single query text, typically used for search queries.
    """
    pool = get_model_pool()

    if not pool.has_embedding:
        raise HTTPException(
            status_code=settings.status_codes.service_unavailable,
            detail=f"Embedding model not available. Service role: {pool.role.value}",
        )

    try:
        provider = pool.get_embedding_provider()
        embedding = await provider.embed_query(request.text)

        return EmbedQueryResponse(
            embedding=list(embedding),
            model=settings.embedding.model_name,
            dimension=settings.embedding.dimension,
        )
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(
            status_code=settings.status_codes.internal_error,
            detail=f"Query embedding failed: {e}",
        )


# ---------------------------------------------------------------------------
# Reranker Routes
# ---------------------------------------------------------------------------


@app.post("/v1/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank documents by relevance to a query.

    Uses a cross-encoder model to score each (query, document) pair
    and returns results sorted by relevance score (descending).
    """
    pool = get_model_pool()

    if not pool.has_reranker:
        raise HTTPException(
            status_code=settings.status_codes.service_unavailable,
            detail=f"Reranker model not available. Service role: {pool.role.value}",
        )

    try:
        provider = pool.get_reranker_provider()

        # Use the reranker's rerank method
        scored_results = await provider.rerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k,
        )

        # Build response — scored_results should be list of (index, score) or similar
        results = []
        for item in scored_results:
            # Handle different return formats from the reranker provider
            if isinstance(item, dict):
                idx = item.get("index", item.get("corpus_id", 0))
                score = item.get("score", item.get("relevance_score", 0.0))
            elif hasattr(item, "index"):
                idx = item.index
                score = item.score
            else:
                # Assume tuple (index, score)
                idx, score = item[0], item[1]

            results.append(RerankResult(
                index=idx,
                score=score,
                text=request.documents[idx] if idx < len(request.documents) else "",
            ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Apply top_k if specified
        if request.top_k is not None:
            results = results[: request.top_k]

        return RerankResponse(
            results=results,
            model=settings.reranker.model_name,
            count=len(results),
        )
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(
            status_code=settings.status_codes.internal_error,
            detail=f"Reranking inference failed: {e}",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Force Proactor loop for Windows subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main():
    """Run the ML Inference service."""
    import uvicorn
    uvicorn.run(
        "services.ml_inference.main:app",
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.ML_INFERENCE),
        reload=False,
    )


if __name__ == "__main__":
    main()
