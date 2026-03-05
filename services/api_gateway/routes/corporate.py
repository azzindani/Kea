"""
Corporate Route — API Gateway proxy to Corporate Gateway Service.

Proxies all /corporate/* requests to the Corporate Gateway Service (:8010).
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.schemas import CorporateProcessRequest
from shared.service_registry import ServiceName, ServiceRegistry

log = get_logger(__name__)

router = APIRouter(prefix="/corporate", tags=["Corporate"])


async def _proxy_to_gateway(
    method: str,
    path: str,
    json_body: Any = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Proxy request to Corporate Gateway Service."""
    settings = get_settings()
    gateway_url = ServiceRegistry.get_url(ServiceName.CORPORATE_GATEWAY)
    timeout = settings.corporate.corporate_ops_timeout_ms / 1000.0

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            kwargs: dict[str, Any] = {}
            if json_body is not None:
                kwargs["json"] = json_body
            if params:
                kwargs["params"] = params

            response = await client.request(
                method, f"{gateway_url}/corporate{path}", **kwargs
            )
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Corporate Gateway timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Corporate Gateway unreachable")
    except Exception as exc:
        log.error("corporate_proxy_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/process")
async def corporate_process(request: CorporateProcessRequest) -> dict[str, Any]:
    """THE entry point — proxy to Corporate Gateway Service."""
    return await _proxy_to_gateway(
        "POST", "/process", json_body=request.model_dump()
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Get session state — proxy."""
    return await _proxy_to_gateway("GET", f"/sessions/{session_id}")


@router.get("/missions/{mission_id}/status")
async def get_mission_status(mission_id: str) -> dict[str, Any]:
    """Mission status — proxy."""
    return await _proxy_to_gateway(
        "GET", f"/missions/{mission_id}/status"
    )


@router.post("/missions/{mission_id}/interrupt")
async def send_interrupt(
    mission_id: str,
    content: str = "",
) -> dict[str, Any]:
    """Send interrupt — proxy."""
    return await _proxy_to_gateway(
        "POST",
        f"/missions/{mission_id}/interrupt",
        params={"content": content},
    )


@router.get("/history/{client_id}")
async def get_client_history(client_id: str) -> list[dict[str, Any]]:
    """Client history — proxy."""
    result = await _proxy_to_gateway("GET", f"/history/{client_id}")
    return result if isinstance(result, list) else []
