"""
Embedding & Reranker HTTP Clients.

Lightweight HTTP clients that implement the EmbeddingProvider and
RerankerProvider interfaces by calling the ML Inference service.

These clients contain ZERO PyTorch/Transformers dependencies — they
use only httpx for HTTP communication. This is the module that
consumer services (Vault, MCP Host, RAG) should use instead of
loading models in-process.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Concurrency Guard
# ---------------------------------------------------------------------------
# The ML Inference service processes GPU requests sequentially.  When
# multiple callers (tool-registry + knowledge-registry) fire concurrent
# embedding requests, the single-threaded GPU handler causes TCP-level
# connection resets (httpx.ReadError).  A module-level semaphore limits
# in-flight embedding requests so they are serialized cleanly.
# ---------------------------------------------------------------------------
_EMBED_MAX_CONCURRENT: int = 1
_embed_semaphore: asyncio.Semaphore | None = None


def _get_embed_semaphore() -> asyncio.Semaphore:
    """Lazy-init a per-loop semaphore to serialize GPU embedding calls."""
    global _embed_semaphore
    if _embed_semaphore is None:
        _embed_semaphore = asyncio.Semaphore(_EMBED_MAX_CONCURRENT)
    return _embed_semaphore


class EmbeddingServiceClient:
    """
    HTTP client for the ML Inference embedding endpoints.

    Implements the same interface as EmbeddingProvider (embed, embed_query)
    so it can be used as a drop-in replacement.

    Features:
    - Connection pooling via httpx.AsyncClient
    - Configurable timeouts from shared.config
    - Automatic retry on transient failures
    """

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base_url = base_url or ServiceRegistry.get_url(ServiceName.ML_INFERENCE)
        self._timeout = httpx.Timeout(
            settings.timeouts.embedding_api,
            connect=settings.timeouts.short,
        )
        self._max_retries = settings.circuit_breaker.failure_threshold
        self._retry_delay: float = 1.0
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent HTTP client, ensuring it matches the current loop."""
        current_loop = asyncio.get_running_loop()
        
        if self._client is None or self._client.is_closed or self._loop != current_loop:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
            
            settings = get_settings()
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=settings.api.max_connections,
                    max_keepalive_connections=settings.api.max_connections // 2,
                ),
            )
            self._loop = current_loop
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry on transient failures."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.request(method, path, **kwargs)

                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                return response

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,
                httpx.ReadError,
            ) as e:
                last_error = e
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        f"ML Inference request failed (attempt {attempt + 1}) "
                        f"at {self._base_url}{path}: {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_error or Exception("ML Inference request failed after retries")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts via the ML Inference service.

        Serialized via a module-level semaphore to prevent concurrent
        GPU requests from causing TCP connection resets (ReadError).

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        async with _get_embed_semaphore():
            response = await self._request_with_retry(
                "POST",
                "/v1/embed",
                json={"texts": texts},
            )
        if response.status_code != 200:
            error_msg = f"ML Inference Service Error ({response.status_code}) at {self._base_url}/v1/embed"
            try:
                detail = response.json().get("detail", "No detail provided")
                error_msg += f": {detail}"
            except Exception:
                pass
            raise RuntimeError(error_msg)

        data = response.json()
        if "embeddings" not in data:
            raise KeyError(f"Expected 'embeddings' key in response from {self._base_url}/v1/embed, but got: {list(data.keys())}")
        return data["embeddings"]

    async def embed_query(self, query: str) -> list[float]:
        """
        Embed a single query text via the ML Inference service.

        Serialized via the same semaphore as embed() to prevent
        contention on the single GPU inference pipeline.

        Args:
            query: Query text to embed.

        Returns:
            Embedding vector (list of floats).
        """
        async with _get_embed_semaphore():
            response = await self._request_with_retry(
                "POST",
                "/v1/embed/query",
                json={"text": query},
            )
        if response.status_code != 200:
            error_msg = f"ML Inference Service Error ({response.status_code}) at {self._base_url}/v1/embed/query"
            try:
                detail = response.json().get("detail", "No detail provided")
                error_msg += f": {detail}"
            except Exception:
                pass
            raise RuntimeError(error_msg)

        data = response.json()
        if "embedding" not in data:
            raise KeyError(f"Expected 'embedding' key in response from {self._base_url}/v1/embed/query, but got: {list(data.keys())}")
        return data["embedding"]

    async def is_available(self) -> bool:
        """Check if the ML Inference service is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == get_settings().status_codes.ok
        except (httpx.HTTPError, asyncio.TimeoutError):
            return False
        except Exception as e:
            logger.debug(f"Unexpected error checking ML Inference availability: {e}")
            return False


class RerankerServiceClient:
    """
    HTTP client for the ML Inference reranker endpoint.

    Implements the same interface as RerankerProvider (rerank)
    so it can be used as a drop-in replacement.
    """

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base_url = base_url or ServiceRegistry.get_url(ServiceName.ML_RERANKER)
        self._timeout = httpx.Timeout(
            settings.timeouts.embedding_api,
            connect=settings.timeouts.short,
        )
        self._max_retries = settings.circuit_breaker.failure_threshold
        self._retry_delay: float = 1.0
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent HTTP client, ensuring it matches the current loop."""
        current_loop = asyncio.get_running_loop()
        
        if self._client is None or self._client.is_closed or self._loop != current_loop:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
                
            settings = get_settings()
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=settings.api.max_connections,
                    max_keepalive_connections=settings.api.max_connections // 2,
                ),
            )
            self._loop = current_loop
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry on transient failures."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.request(method, path, **kwargs)

                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                return response

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,
                httpx.ReadError,
            ) as e:
                last_error = e
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        f"ML Reranker request failed (attempt {attempt + 1}) "
                        f"at {self._base_url}{path}: {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_error or Exception("ML Reranker request failed after retries")

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Rerank documents by relevance to a query via the ML Inference service.

        Args:
            query: The search query.
            documents: List of document texts to rerank.
            top_k: Optional limit on results.

        Returns:
            List of dicts with 'index', 'score', 'text' sorted by relevance.
        """
        payload: dict[str, Any] = {
            "query": query,
            "documents": documents,
        }
        if top_k is not None:
            payload["top_k"] = top_k

        response = await self._request_with_retry(
            "POST",
            "/v1/rerank",
            json=payload,
        )
        if response.status_code != 200:
            error_msg = f"ML Inference Service Error ({response.status_code}) at {self._base_url}/v1/rerank"
            try:
                detail = response.json().get("detail", "No detail provided")
                error_msg += f": {detail}"
            except Exception:
                pass
            raise RuntimeError(error_msg)

        data = response.json()
        if "results" not in data:
            raise KeyError(f"Expected 'results' key in response from {self._base_url}/v1/rerank, but got: {list(data.keys())}")
        return data["results"]

    async def is_available(self) -> bool:
        """Check if the ML Inference reranker service is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == get_settings().status_codes.ok
        except (httpx.HTTPError, asyncio.TimeoutError):
            return False
        except Exception as e:
            logger.debug(f"Unexpected error checking ML Reranker availability: {e}")
            return False


# ---------------------------------------------------------------------------
# Module-level Singletons
# ---------------------------------------------------------------------------

_embedding_client: EmbeddingServiceClient | None = None
_reranker_client: RerankerServiceClient | None = None


def get_embedding_client() -> EmbeddingServiceClient:
    """Get singleton EmbeddingServiceClient."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingServiceClient()
    return _embedding_client


def get_reranker_client() -> RerankerServiceClient:
    """Get singleton RerankerServiceClient."""
    global _reranker_client
    if _reranker_client is None:
        _reranker_client = RerankerServiceClient()
    return _reranker_client
