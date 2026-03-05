"""
ML Inference Service — API Schemas.

Pydantic request/response models for the embedding and reranking endpoints.
All models follow shared.schemas conventions: strict types, immutable defaults.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from shared.config import get_settings


# ---------------------------------------------------------------------------
# Embedding Schemas
# ---------------------------------------------------------------------------


class EmbedRequest(BaseModel):
    """Batch text embedding request."""
    texts: list[str] = Field(
        ...,
        min_length=1,
        description="List of texts to embed",
    )
    instruction: str | None = Field(
        default=None,
        description="Optional task instruction prepended to each text",
    )


class EmbedQueryRequest(BaseModel):
    """Single query embedding request (convenience endpoint)."""
    text: str = Field(
        ...,
        min_length=1,
        description="Query text to embed",
    )
    instruction: str | None = Field(
        default=None,
        description="Optional task instruction prepended to the query",
    )


class EmbedResponse(BaseModel):
    """Embedding response."""
    embeddings: list[list[float]] = Field(
        ...,
        description="List of embedding vectors",
    )
    model: str = Field(
        ...,
        description="Model name used for embedding",
    )
    dimension: int = Field(
        ...,
        description="Embedding vector dimension",
    )
    count: int = Field(
        ...,
        description="Number of texts embedded",
    )


class EmbedQueryResponse(BaseModel):
    """Single query embedding response."""
    embedding: list[float] = Field(
        ...,
        description="Embedding vector for the query",
    )
    model: str = Field(
        ...,
        description="Model name used for embedding",
    )
    dimension: int = Field(
        ...,
        description="Embedding vector dimension",
    )


# ---------------------------------------------------------------------------
# Reranker Schemas
# ---------------------------------------------------------------------------


class RerankRequest(BaseModel):
    """Reranking request."""
    query: str = Field(
        ...,
        min_length=1,
        description="Query to rerank documents against",
    )
    documents: list[str] = Field(
        ...,
        min_length=1,
        description="List of documents to rerank",
    )
    top_k: int | None = Field(
        default=None,
        description="Number of top results to return (default: all)",
    )
    instruction: str | None = Field(
        default=None,
        description="Optional task instruction for reranking",
    )


class RerankResult(BaseModel):
    """A single reranked document result."""
    index: int = Field(..., description="Original index of the document")
    score: float = Field(..., description="Relevance score")
    text: str = Field(..., description="Document text")


class RerankResponse(BaseModel):
    """Reranking response."""
    results: list[RerankResult] = Field(
        ...,
        description="Documents sorted by relevance score (descending)",
    )
    model: str = Field(
        ...,
        description="Model name used for reranking",
    )
    count: int = Field(
        ...,
        description="Number of documents reranked",
    )


# ---------------------------------------------------------------------------
# Model Info Schemas
# ---------------------------------------------------------------------------


class ModelInfo(BaseModel):
    """Information about a loaded model."""
    name: str = Field(..., description="Model identifier")
    role: str = Field(..., description="Model role: embedding | reranker")
    device: str = Field(..., description="Device model is loaded on")
    loaded: bool = Field(..., description="Whether the model is loaded and ready")
    dimension: int | None = Field(
        default=None,
        description="Embedding dimension (embedding models only)",
    )


class ModelsResponse(BaseModel):
    """Response for the models listing endpoint."""
    models: list[ModelInfo] = Field(
        default_factory=list,
        description="List of available models",
    )
    service_role: str = Field(
        ...,
        description="Service role: embedding | reranker | both",
    )


# ---------------------------------------------------------------------------
# Health Schemas
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health check response with model and device status."""
    status: str = Field(..., description="Service status: ok | degraded | error")
    service: str = Field(default="ml_inference", description="Service name")
    role: str = Field(..., description="Service role: embedding | reranker | both")
    models_loaded: int = Field(..., description="Number of models loaded")
    device: str = Field(..., description="Primary compute device")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
