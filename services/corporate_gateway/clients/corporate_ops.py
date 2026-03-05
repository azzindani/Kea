"""
Corporate Ops HTTP Client — Corporate Gateway → Corporate Ops.

Full-featured client following the architecture plan.
Handles mission lifecycle, status polling, interrupts, and quality audits.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

log = get_logger(__name__)


class CorporateOpsClient:
    """HTTP client for the Corporate Operations Service (:8011).

    Covers:
      - POST /orchestration/missions         (start)
      - GET  /orchestration/missions/{id}/status  (poll)
      - POST /orchestration/missions/{id}/interrupt
      - POST /orchestration/missions/{id}/abort
      - POST /orchestration/missions/{id}/resume
      - POST /quality/audit/mission/{id}     (final audit)
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or ServiceRegistry.get_url(
            ServiceName.CORPORATE_OPS
        )
        settings = get_settings()
        self._timeout = settings.corporate.corporate_ops_timeout_ms / 1000.0
        self._max_retries = settings.corporate.http_max_retries
        self._retry_base = settings.corporate.http_retry_base_delay
        self._log = log

    # ================================================================
    # Transport
    # ================================================================

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
                        "corporate_ops_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        path=path,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    # ================================================================
    # Mission Lifecycle
    # ================================================================

    async def start_mission(
        self,
        mission_data: dict[str, Any],
    ) -> dict[str, Any]:
        """POST /api/v1/orchestration/missions — Delegate full mission execution."""
        response = await self._request(
            "POST", "/api/v1/orchestration/missions", json=mission_data
        )
        return response.json()

    async def get_mission_status(self, mission_id: str) -> dict[str, Any]:
        """GET /api/v1/orchestration/missions/{id}/status."""
        response = await self._request(
            "GET", f"/api/v1/orchestration/missions/{mission_id}/status"
        )
        return response.json()

    async def send_interrupt(
        self,
        mission_id: str,
        interrupt_data: dict[str, Any],
    ) -> dict[str, Any]:
        """POST /api/v1/orchestration/missions/{id}/interrupt (scope change / abort signal)."""
        try:
            response = await self._request(
                "POST",
                f"/api/v1/orchestration/missions/{mission_id}/interrupt",
                json=interrupt_data,
            )
            return response.json()
        except Exception as exc:
            self._log.warning("interrupt_failed", mission_id=mission_id, error=str(exc))
            return {"status": "interrupt_failed", "error": str(exc)}

    async def abort_mission(self, mission_id: str) -> dict[str, Any]:
        """POST /api/v1/orchestration/missions/{id}/abort."""
        try:
            response = await self._request(
                "POST", f"/api/v1/orchestration/missions/{mission_id}/abort"
            )
            return response.json()
        except Exception as exc:
            self._log.warning("abort_failed", mission_id=mission_id, error=str(exc))
            return {"status": "abort_failed", "error": str(exc)}

    async def resume_mission(self, mission_id: str) -> dict[str, Any]:
        """POST /api/v1/orchestration/missions/{id}/resume."""
        response = await self._request(
            "POST", f"/api/v1/orchestration/missions/{mission_id}/resume"
        )
        return response.json()

    # ================================================================
    # Quality Audit
    # ================================================================

    async def audit_mission(self, mission_id: str) -> dict[str, Any]:
        """POST /api/v1/quality/audit/mission/{id} — final quality audit."""
        try:
            response = await self._request(
                "GET", f"/api/v1/quality/audit/mission/{mission_id}"
            )
            return response.json()
        except Exception as exc:
            self._log.warning("audit_failed", mission_id=mission_id, error=str(exc))
            return {
                "overall_score": 0.0,
                "sprints": [],
                "conflicts_found": 0,
                "gaps": [],
            }


# ============================================================================
# Singleton
# ============================================================================

_client: CorporateOpsClient | None = None


async def get_corporate_ops_client() -> CorporateOpsClient:
    """Get the singleton Corporate Ops client."""
    global _client
    if _client is None:
        _client = CorporateOpsClient()
    return _client
