"""
Vault Ledger Client — Corporate Artifact Management.

HTTP client for the Vault Service's persistence API.
Handles artifact storage, checkpoint persistence, session management,
and semantic recall with production-grade retry and backoff.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

log = get_logger(__name__)


# ============================================================================
# Vault Ledger Types (local to this client)
# ============================================================================

from pydantic import BaseModel, Field


class ArtifactMetadata(BaseModel):
    """Metadata for a Vault-stored artifact."""

    team_id: str = Field(default="", description="Team/pool identifier")
    mission_id: str = Field(default="", description="Parent mission")
    sprint_id: str | None = Field(default=None)
    chunk_id: str | None = Field(default=None)
    agent_id: str = Field(default="", description="Producing agent")
    content_type: str = Field(
        default="report",
        description="code | analysis | report | data | review",
    )
    topic: str = Field(default="", description="Semantic category")
    summary: str = Field(default="", description="Brief description for indexing")


class VaultArtifact(BaseModel):
    """An artifact retrieved from Vault."""

    artifact_id: str = Field(default="")
    content: str = Field(default="")
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)
    created_utc: str = Field(default="")


class CheckpointState(BaseModel):
    """Serializable mission state for persistence."""

    mission_id: str = Field(default="")
    current_sprint: int = Field(default=0, ge=0)
    total_sprints: int = Field(default=0, ge=0)
    completed_chunk_ids: list[str] = Field(default_factory=list)
    failed_chunk_ids: list[str] = Field(default_factory=list)
    pool_snapshot: dict[str, Any] = Field(default_factory=dict)
    artifact_ids: list[str] = Field(default_factory=list)
    total_cost: float = Field(default=0.0, ge=0.0)
    elapsed_ms: float = Field(default=0.0, ge=0.0)
    checkpointed_utc: str = Field(default="")


# ============================================================================
# HTTP Client
# ============================================================================


class VaultLedgerClient:
    """HTTP client for Vault Service — corporate artifact management.

    Follows the existing project pattern from
    services/api_gateway/clients/orchestrator.py with retry + backoff.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or ServiceRegistry.get_url(ServiceName.VAULT)
        settings = get_settings()
        self._timeout = settings.corporate.vault_timeout_ms / 1000.0
        self._max_retries = settings.corporate.http_max_retries
        self._retry_base = settings.corporate.http_retry_base_delay
        self._log = log

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """HTTP request with retry + exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout
                ) as client:
                    response = await client.request(
                        method, f"{self._base_url}{path}", **kwargs
                    )
                    response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = self._retry_base * (2**attempt)
                    self._log.warning(
                        "vault_request_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    # ====================================================================
    # Artifact Operations
    # ====================================================================

    async def write_artifact(
        self,
        agent_id: str,
        team_id: str,
        content: str,
        metadata: ArtifactMetadata,
    ) -> str:
        """Write an artifact to Vault.

        Returns the artifact ID.
        HTTP POST vault/persistence/sessions
        """
        payload = {
            "agent_id": agent_id,
            "team_id": team_id,
            "content": content,
            "metadata": metadata.model_dump(),
            "type": "artifact",
        }
        response = await self._request(
            "POST", "/persistence/sessions", json=payload
        )
        data = response.json()
        return data.get("id", data.get("artifact_id", ""))

    async def read_artifacts(
        self,
        team_id: str,
        query: str | None = None,
        topic: str | None = None,
        limit: int | None = None,
    ) -> list[VaultArtifact]:
        """Read artifacts from Vault.

        HTTP GET vault/persistence/query
        """
        params: dict[str, Any] = {"team_id": team_id}
        if query:
            params["query"] = query
        if topic:
            params["topic"] = topic
        if limit:
            params["limit"] = limit

        response = await self._request(
            "GET", "/persistence/query", params=params
        )
        data = response.json()
        results = data if isinstance(data, list) else data.get("results", [])
        return [VaultArtifact(**r) for r in results]

    # ====================================================================
    # Checkpoint Operations
    # ====================================================================

    async def write_checkpoint(
        self,
        mission_id: str,
        state: CheckpointState,
    ) -> str:
        """Write a mission checkpoint to Vault.

        Returns the checkpoint ID.
        HTTP POST vault/persistence/sessions
        """
        payload = {
            "mission_id": mission_id,
            "state": state.model_dump(),
            "type": "checkpoint",
        }
        response = await self._request(
            "POST", "/persistence/sessions", json=payload
        )
        data = response.json()
        return data.get("id", data.get("checkpoint_id", ""))

    async def read_checkpoint(
        self, mission_id: str
    ) -> CheckpointState | None:
        """Read the latest checkpoint for a mission.

        HTTP GET vault/persistence/query
        """
        try:
            response = await self._request(
                "GET",
                "/persistence/query",
                params={"mission_id": mission_id, "type": "checkpoint", "limit": 1},
            )
            data = response.json()
            results = data if isinstance(data, list) else data.get("results", [])
            if results:
                state_data = results[0].get("state", results[0])
                return CheckpointState(**state_data)
            return None
        except Exception:
            self._log.warning(
                "checkpoint_read_failed", mission_id=mission_id
            )
            return None

    # ====================================================================
    # Semantic Recall
    # ====================================================================

    async def recall_memory(
        self,
        client_id: str,
        query: str,
        limit: int | None = None,
    ) -> list[VaultArtifact]:
        """Semantic search across all artifacts.

        HTTP GET vault/persistence/query (semantic search)
        """
        params: dict[str, Any] = {
            "client_id": client_id,
            "query": query,
            "search_mode": "semantic",
        }
        if limit:
            params["limit"] = limit

        response = await self._request(
            "GET", "/persistence/query", params=params
        )
        data = response.json()
        results = data if isinstance(data, list) else data.get("results", [])
        return [VaultArtifact(**r) for r in results]


# ============================================================================
# Singleton
# ============================================================================

_client: VaultLedgerClient | None = None


async def get_vault_ledger_client() -> VaultLedgerClient:
    """Get the singleton Vault Ledger client."""
    global _client
    if _client is None:
        _client = VaultLedgerClient()
    return _client
