"""
Orchestrator Service Client.

HTTP client for calling the Orchestrator service with production features:
- Connection pooling
- Retry with exponential backoff
- Circuit breaker
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from shared.config import Settings

import httpx

from shared.logging import get_logger
from shared.config import get_settings
from shared.environment import get_environment_config


logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    failure_threshold: int = 5
    reset_timeout: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure: float = 0.0
    
    def __post_init__(self):
        from shared.config import get_settings
        settings = get_settings()
        self.failure_threshold = settings.circuit_breaker.failure_threshold
        self.reset_timeout = settings.circuit_breaker.reset_timeout
    
    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened")
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True


class OrchestratorClient:
    """
    HTTP client for the Orchestrator service.
    
    Features:
    - Connection pooling
    - Retry with exponential backoff
    - Circuit breaker
    - Streaming support
    """
    
    def __init__(self, base_url: str | None = None) -> None:
        from shared.service_registry import ServiceRegistry, ServiceName
        
        self.base_url = base_url or ServiceRegistry.get_url(ServiceName.ORCHESTRATOR)
        
        settings = get_settings()
        self.timeout = httpx.Timeout(
            settings.timeouts.default,
            connect=settings.timeouts.auth_token,
        )
        # Using long timeout for research jobs if needed, but default for health/tools
        self.research_timeout = settings.timeouts.long
        
        self.max_retries = settings.mcp.max_retries
        self.retry_delay = settings.mcp.retry_delay
        
        self._circuit = CircuitBreaker()
        self.settings = settings
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create pooled client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=self.settings.api.max_connections),
            )
        return self._client
    
    async def close(self):
        """Close client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> httpx.Response:
        """Make request with retry and circuit breaker."""
        if not self._circuit.can_execute():
            raise Exception("Circuit breaker open")
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.request(method, path, **kwargs)
                
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                
                self._circuit.record_success()
                return response
                
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                last_error = e
                self._circuit.record_failure()
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}: {e}")
                    await asyncio.sleep(delay)
        
        raise last_error or Exception("Request failed")
    
    async def health_check(self) -> dict[str, Any]:
        """Check orchestrator health."""
        response = await self._request("GET", "/health")
        return response.json()
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """Get list of available MCP tools."""
        response = await self._request("GET", "/tools")
        return response.json().get("tools", [])
    
    async def start_research(
        self,
        query: str,
        depth: int | None = None,
        max_sources: int | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        depth = depth or settings.research.default_depth
        max_sources = max_sources or settings.research.default_max_sources
        
        response = await self._request(
            "POST",
            "/research",
            json={"query": query, "depth": depth, "max_sources": max_sources},
        )
        return response.json()
    
    async def stream_research(
        self,
        query: str,
        depth: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream research results via SSE."""
        settings = get_settings()
        depth = depth or settings.research.default_depth
        
        client = await self._get_client()
        
        async with client.stream(
            "GET",
            "/research/stream",
            params={"query": query, "depth": depth},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call an MCP tool directly."""
        response = await self._request(
            "POST",
            f"/tools/{tool_name}",
            json=arguments,
        )
        return response.json()


# Singleton
_client: OrchestratorClient | None = None


async def get_orchestrator_client() -> OrchestratorClient:
    """Get singleton client."""
    global _client
    if _client is None:
        _client = OrchestratorClient()
    return _client

