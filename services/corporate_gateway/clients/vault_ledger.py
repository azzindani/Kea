"""
Vault Ledger HTTP Client — Corporate Gateway → Vault Service.

Handles session management, artifact retrieval, result persistence,
and audit logging for the Corporate Gateway.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

log = get_logger(__name__)


# ============================================================================
# Local Types
# ============================================================================


class VaultArtifact(BaseModel):
    """An artifact retrieved from Vault."""

    artifact_id: str = Field(default="")
    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_utc: str = Field(default="")


class VaultSession(BaseModel):
    """A session record from Vault."""

    session_id: str = Field(default="")
    client_id: str = Field(default="")
    turns: int = Field(default=0)
    active_mission_id: str | None = Field(default=None)
    history_artifact_ids: list[str] = Field(default_factory=list)
    last_intent: str | None = Field(default=None)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


# ============================================================================
# HTTP Client
# ============================================================================


class VaultLedgerClient:
    """HTTP client for Vault Service — Corporate Gateway session/artifact access."""

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
                async with httpx.AsyncClient(timeout=self._timeout) as client:
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
                        "vault_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    # ================================================================
    # Session Management
    # ================================================================

    async def load_session(
        self,
        session_id: str | None = None,
        client_id: str | None = None,
    ) -> VaultSession | None:
        """Load session context from Vault.

        HTTP GET vault/persistence/query
        """
        params: dict[str, Any] = {"type": "session"}
        if session_id:
            params["session_id"] = session_id
        if client_id:
            params["client_id"] = client_id

        try:
            response = await self._request(
                "GET", "/persistence/query", params=params
            )
            data = response.json()
            results = data if isinstance(data, list) else data.get("results", [])
            if results:
                return VaultSession(**results[0])
            return None
        except Exception:
            self._log.warning("session_load_failed",
                              session_id=session_id,
                              client_id=client_id)
            return None

    async def persist_session(
        self,
        session: VaultSession,
    ) -> str:
        """Persist session state to Vault.

        HTTP POST vault/persistence/sessions
        """
        payload = {
            "type": "session",
            **session.model_dump(),
        }
        response = await self._request(
            "POST", "/persistence/sessions", json=payload
        )
        data = response.json()
        return data.get("id", data.get("session_id", ""))

    # ================================================================
    # Artifact Operations
    # ================================================================

    async def collect_artifacts(
        self,
        mission_id: str,
        limit: int | None = None,
    ) -> list[VaultArtifact]:
        """Collect all artifacts for a mission.

        HTTP GET vault/persistence/query
        """
        params: dict[str, Any] = {
            "mission_id": mission_id,
            "type": "artifact",
        }
        if limit:
            params["limit"] = limit

        try:
            response = await self._request(
                "GET", "/persistence/query", params=params
            )
            data = response.json()
            results = data if isinstance(data, list) else data.get("results", [])
            return [VaultArtifact(**r) for r in results]
        except Exception:
            self._log.warning("artifact_collect_failed",
                              mission_id=mission_id)
            return []

    async def persist_result(
        self,
        mission_id: str,
        result_data: dict[str, Any],
    ) -> str:
        """Persist the final corporate result artifact to Vault.

        HTTP POST vault/persistence/sessions
        """
        payload = {
            "type": "corporate_result",
            "mission_id": mission_id,
            **result_data,
        }
        response = await self._request(
            "POST", "/persistence/sessions", json=payload
        )
        data = response.json()
        return data.get("id", data.get("artifact_id", ""))

    # ================================================================
    # Semantic Recall
    # ================================================================

    async def recall_memory(
        self,
        client_id: str,
        query: str,
        limit: int = 5,
    ) -> list[VaultArtifact]:
        """Semantic search across all of a client's artifacts.

        HTTP GET vault/persistence/query
        """
        params: dict[str, Any] = {
            "client_id": client_id,
            "query": query,
            "search_mode": "semantic",
            "limit": limit,
        }

        try:
            response = await self._request(
                "GET", "/persistence/query", params=params
            )
            data = response.json()
            results = data if isinstance(data, list) else data.get("results", [])
            return [VaultArtifact(**r) for r in results]
        except Exception:
            self._log.warning("memory_recall_failed",
                              client_id=client_id, query=query)
            return []

    # ================================================================
    # Audit Logging
    # ================================================================

    async def write_audit_log(
        self,
        mission_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        """Write an audit trail entry to Vault.

        HTTP POST vault/audit/logs
        """
        payload = {
            "mission_id": mission_id,
            "event_type": event_type,
            "details": details,
        }
        try:
            await self._request("POST", "/audit/logs", json=payload)
        except Exception:
            self._log.warning("audit_log_failed",
                              mission_id=mission_id,
                              event_type=event_type)

    # ================================================================
    # Client History
    # ================================================================

    async def get_client_history(
        self,
        client_id: str,
        limit: int = 20,
    ) -> list[VaultArtifact]:
        """Retrieve client interaction history.

        HTTP GET vault/persistence/query
        """
        params: dict[str, Any] = {
            "client_id": client_id,
            "type": "corporate_result",
            "limit": limit,
        }

        try:
            response = await self._request(
                "GET", "/persistence/query", params=params
            )
            data = response.json()
            results = data if isinstance(data, list) else data.get("results", [])
            return [VaultArtifact(**r) for r in results]
        except Exception:
            self._log.warning("history_fetch_failed",
                              client_id=client_id)
            return []


# ============================================================================
# Singleton
# ============================================================================

_client: VaultLedgerClient | None = None


async def get_vault_client() -> VaultLedgerClient:
    """Get the singleton Vault Ledger client."""
    global _client
    if _client is None:
        _client = VaultLedgerClient()
    return _client
