"""
Orchestrator Service Client — Corporate Agent API.

HTTP client for the Orchestrator's corporate agent endpoints.
Handles agent spawning, execution, status polling, and termination
with production-grade retry, backoff, and circuit breaking.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.schemas import (
    CorporateAgentProcessRequest,
    CorporateAgentProcessResponse,
    CorporateAgentSpawnRequest,
    CorporateAgentSpawnResponse,
    CorporateAgentStatusResponse,
)
from shared.service_registry import ServiceName, ServiceRegistry

log = get_logger(__name__)


class _CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class _CircuitBreaker:
    """Lightweight circuit breaker for the Orchestrator connection."""

    failure_threshold: int = field(init=False)
    reset_timeout: float = field(init=False)
    state: _CircuitState = _CircuitState.CLOSED
    failure_count: int = 0
    last_failure: float = 0.0

    def __post_init__(self) -> None:
        settings = get_settings()
        self.failure_threshold = settings.circuit_breaker.failure_threshold
        self.reset_timeout = settings.circuit_breaker.reset_timeout

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = _CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = _CircuitState.OPEN
            log.warning("corporate_orchestrator_circuit_open")

    def can_execute(self) -> bool:
        if self.state == _CircuitState.CLOSED:
            return True
        if self.state == _CircuitState.OPEN:
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = _CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: allow probe


class CorporateOrchestratorClient:
    """HTTP client for the Orchestrator's /corporate/agents API.

    Provides typed methods for spawning, executing, polling, and
    terminating corporate specialist agents via the Orchestrator
    Service's HTTP boundary.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or ServiceRegistry.get_url(
            ServiceName.ORCHESTRATOR
        )
        settings = get_settings()
        self._timeout = settings.corporate.orchestrator_timeout_ms / 1000.0
        self._max_retries = settings.corporate.http_max_retries
        self._retry_base = settings.corporate.http_retry_base_delay
        self._circuit = _CircuitBreaker()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """HTTP request with retry + exponential backoff + circuit breaker."""
        if not self._circuit.can_execute():
            raise ConnectionError("Circuit breaker open for Orchestrator")

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

                self._circuit.record_success()
                return response

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,
            ) as exc:
                last_error = exc
                self._circuit.record_failure()

                if attempt < self._max_retries:
                    delay = self._retry_base * (2**attempt)
                    log.warning(
                        "orchestrator_request_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        raise last_error or ConnectionError("Orchestrator request failed")

    # ====================================================================
    # Corporate Agent Lifecycle
    # ====================================================================

    async def spawn_agent(
        self, request: CorporateAgentSpawnRequest
    ) -> CorporateAgentSpawnResponse:
        """Spawn a Human Kernel specialist.

        HTTP POST /corporate/agents
        """
        response = await self._request(
            "POST",
            "/corporate/agents",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return CorporateAgentSpawnResponse(**response.json())

    async def spawn_batch(
        self, requests: list[CorporateAgentSpawnRequest]
    ) -> list[CorporateAgentSpawnResponse]:
        """Spawn multiple specialists in batch.

        HTTP POST /corporate/agents/batch
        """
        response = await self._request(
            "POST",
            "/corporate/agents/batch",
            json=[r.model_dump() for r in requests],
        )
        response.raise_for_status()
        return [CorporateAgentSpawnResponse(**r) for r in response.json()]

    async def process_agent(
        self,
        agent_id: str,
        request: CorporateAgentProcessRequest,
    ) -> CorporateAgentProcessResponse:
        """Execute ConsciousObserver.process() on a spawned agent.

        HTTP POST /corporate/agents/{agent_id}/process
        """
        response = await self._request(
            "POST",
            f"/corporate/agents/{agent_id}/process",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return CorporateAgentProcessResponse(**response.json())

    async def get_agent_status(
        self, agent_id: str
    ) -> CorporateAgentStatusResponse:
        """Get agent heartbeat/status.

        HTTP GET /corporate/agents/{agent_id}/status
        """
        response = await self._request(
            "GET",
            f"/corporate/agents/{agent_id}/status",
        )
        response.raise_for_status()
        return CorporateAgentStatusResponse(**response.json())

    async def get_agent_result(
        self, agent_id: str
    ) -> CorporateAgentProcessResponse:
        """Get completed agent output.

        HTTP GET /corporate/agents/{agent_id}/result
        """
        response = await self._request(
            "GET",
            f"/corporate/agents/{agent_id}/result",
        )
        response.raise_for_status()
        return CorporateAgentProcessResponse(**response.json())

    async def terminate_agent(
        self, agent_id: str, reason: str = "mission_complete"
    ) -> dict[str, Any]:
        """Terminate a specialist.

        HTTP DELETE /corporate/agents/{agent_id}
        """
        response = await self._request(
            "DELETE",
            f"/corporate/agents/{agent_id}",
            params={"reason": reason},
        )
        response.raise_for_status()
        return response.json()

    async def list_pool_agents(
        self, mission_id: str
    ) -> list[CorporateAgentStatusResponse]:
        """List all agents for a mission.

        HTTP GET /corporate/agents/pool/{mission_id}
        """
        response = await self._request(
            "GET",
            f"/corporate/agents/pool/{mission_id}",
        )
        response.raise_for_status()
        return [CorporateAgentStatusResponse(**a) for a in response.json()]


# ============================================================================
# Singleton
# ============================================================================

_client: CorporateOrchestratorClient | None = None


async def get_corporate_orchestrator_client() -> CorporateOrchestratorClient:
    """Get the singleton corporate orchestrator client."""
    global _client
    if _client is None:
        _client = CorporateOrchestratorClient()
    return _client
