"""
Guardrails   compliance gate for tool execution.

Routes compliance checks through the Swarm Manager's REST API (POST /compliance/check)
so the Orchestrator remains decoupled from SwarmManager internals.
Failed compliance checks feed into the existing error_feedback channel rather
than raising exceptions, keeping the self-correction loop intact.
"""

from __future__ import annotations

import httpx

from shared.logging import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)


async def check_tool_call(tool_name: str, arguments: dict) -> list[dict]:
    """
    Gate a single tool call through SwarmManager's compliance API.

    Returns a list of violation dicts (empty = passed).
    Each violation has keys: check_id, severity, message.
    Violations are meant to be appended to error_feedback, not raised.
    """
    try:
        swarm_url = ServiceRegistry.get_url(ServiceName.SWARM_MANAGER)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{swarm_url}/compliance/check",
                json={
                    "operation": "tool_call",
                    "context": {"tool_name": tool_name, "arguments": arguments},
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Compliance check returned {resp.status_code}, treating as passed")
                return []
            data = resp.json()
            if data.get("passed", True):
                return []
            return [
                {
                    "check_id": issue.get("check_id", "unknown"),
                    "severity": issue.get("severity", "warning"),
                    "message": issue.get("message", ""),
                }
                for issue in data.get("issues", [])
            ]
    except Exception as e:
        logger.warning(f"Compliance check failed (non-blocking): {e}")
        return []
