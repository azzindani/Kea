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
# embedding requests, the single-threaded GPU handler can cause TCP-level
# connection resets (httpx.ReadError).
#
# Each Kea service runs in its own thread with its own asyncio event loop,
# so we use a per-loop semaphore dictionary.  This serializes requests
# within each service while cross-service contention is handled by the
# httpx.ReadError retry logic in _request_with_retry().
# ---------------------------------------------------------------------------
_EMBED_MAX_CONCURRENT: int = 1
_embed_semaphores: dict[int, asyncio.Semaphore] = {}


def _get_embed_semaphore() -> asyncio.Semaphore:
    """Get or create a per-event-loop semaphore to serialize GPU embedding calls."""
    loop = asyncio.get_running_loop()
    loop_id = id(loop)
    if loop_id not in _embed_semaphores:
        _embed_semaphores[loop_id] = asyncio.Semaphore(_EMBED_MAX_CONCURRENT)
    return _embed_semaphores[loop_id]


class EmbeddingServiceClient:
    """
    HTTP client for the ML Inference embedding endpoints.

    Implements the same interface as EmbeddingProvider (embed, embed_query)
    so it can be used as a drop-in replacement.

    Features:
    - Per-event-loop connection pooling (thread-safe singleton sharing)
    - Configurable timeouts from shared.config
    - Automatic retry on transient failures

    Thread-safety note
    ------------------
    This instance is typically shared as a process-level singleton via
    model_manager.get_embedding_provider(). Multiple services (RAG, MCP Host,
    Vault) run in separate OS threads, each with their own asyncio event loop.
    The original single self._client approach caused a race condition: thread B
    closing and replacing the client while thread A was mid-request → ReadError.

    Fix: _clients is a dict keyed by event-loop id. Each thread/loop gets its
    own httpx.AsyncClient and never touches another thread's connection pool.
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
        # Per-event-loop clients: id(loop) → httpx.AsyncClient
        self._clients: dict[int, httpx.AsyncClient] = {}

    def _make_client(self) -> httpx.AsyncClient:
        settings = get_settings()
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            limits=httpx.Limits(
                max_connections=settings.api.max_connections,
                max_keepalive_connections=settings.api.max_connections // 2,
            ),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for the current event loop.

        Each asyncio event loop (i.e. each service thread) owns its own
        httpx.AsyncClient so that concurrent threads never close each other's
        connections.
        """
        loop_id = id(asyncio.get_running_loop())
        client = self._clients.get(loop_id)
        if client is None or client.is_closed:
            self._clients[loop_id] = self._make_client()
        return self._clients[loop_id]

    async def close(self) -> None:
        """Close all per-loop HTTP clients and release connections."""
        for client in list(self._clients.values()):
            if not client.is_closed:
                await client.aclose()
        self._clients.clear()

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

    Uses the same per-event-loop client dict pattern as EmbeddingServiceClient
    to prevent cross-thread ReadErrors when the singleton is shared.
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
        # Per-event-loop clients: id(loop) → httpx.AsyncClient
        self._clients: dict[int, httpx.AsyncClient] = {}

    def _make_client(self) -> httpx.AsyncClient:
        settings = get_settings()
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            limits=httpx.Limits(
                max_connections=settings.api.max_connections,
                max_keepalive_connections=settings.api.max_connections // 2,
            ),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for the current event loop."""
        loop_id = id(asyncio.get_running_loop())
        client = self._clients.get(loop_id)
        if client is None or client.is_closed:
            self._clients[loop_id] = self._make_client()
        return self._clients[loop_id]

    async def close(self) -> None:
        """Close all per-loop HTTP clients and release connections."""
        for client in list(self._clients.values()):
            if not client.is_closed:
                await client.aclose()
        self._clients.clear()

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


# ---------------------------------------------------------------------------
# ML Inference Readiness Gate
# ---------------------------------------------------------------------------


async def await_ml_inference_ready() -> None:
    """
    Block until the ML Inference service is healthy (all models loaded).

    Intended for use at the top of background sync jobs in services that
    embed content on startup (RAG knowledge sync, MCP Host tool sync).
    Calling this as the first line of those tasks means the jobs wait
    silently instead of hammering the server with ConnectError retries
    while models are still downloading.

    Config-driven: uses settings.ml_inference.startup_poll_interval and
    settings.ml_inference.startup_health_timeout — no hardcoded values.
    """
    settings = get_settings()
    poll_interval = settings.ml_inference.startup_poll_interval
    timeout = settings.ml_inference.startup_health_timeout
    health_url = f"{ServiceRegistry.get_url(ServiceName.ML_INFERENCE)}/health"

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    attempt = 0

    while loop.time() < deadline:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(health_url)
                if resp.status_code == 200 and resp.json().get("models_loaded", 0) > 0:
                    logger.info(
                        f"ML Inference ready after {attempt} poll(s) — proceeding with sync."
                    )
                    return
                logger.info(
                    f"ML Inference initializing (attempt {attempt}, "
                    f"status={resp.json().get('status', '?')}, "
                    f"models={resp.json().get('models_loaded', 0)}) — "
                    f"retrying in {poll_interval}s..."
                )
        except Exception:
            logger.info(
                f"ML Inference not yet reachable (attempt {attempt}) — "
                f"retrying in {poll_interval}s..."
            )

        await asyncio.sleep(poll_interval)

    logger.warning(
        f"ML Inference did not become ready within {timeout}s. "
        "Proceeding anyway — embedding retries will self-heal."
    )
