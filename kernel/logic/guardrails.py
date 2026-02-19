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


def check_prompt_injection(user_input: str) -> list[str]:
    """
    Detect potential prompt injection attempts.
    
    Returns a list of warning messages if detected.
    """
    warnings = []
    lower_input = user_input.lower()
    
    # Heuristic checks
    risky_phrases = [
        "ignore previous instructions",
        "system override",
        "you are now",
        "developer mode",
        "do anything now",
        "forget all instructions",
    ]
    
    for phrase in risky_phrases:
        if phrase in lower_input:
            warnings.append(f"Prompt Injection Risk: '{phrase}' detected.")
            
    # Length check (very long inputs might be obfuscation)
    if len(user_input) > 10000:
        warnings.append("Input too long (possible DoS/Overloading).")
        
    return warnings


def detect_circular_reasoning(history: list[dict]) -> bool:
    """
    Detect if the agent is stuck in a loop.
    
    Args:
        history: List of tool invocations or plan steps.
        
    Returns:
        True if loop detected.
    """
    if len(history) < 3:
        return False
        
    # Check for identical tool calls in sequence
    last_3 = history[-3:]
    
    # Extract signatures (tool + args)
    signatures = []
    for item in last_3:
        if not isinstance(item, dict):
            continue
        # Handle different history formats
        tool = item.get("tool") or item.get("tool_name")
        args = item.get("args") or item.get("arguments") or item.get("inputs")
        signatures.append(f"{tool}:{str(args)}")
        
    if len(signatures) == 3 and len(set(signatures)) == 1:
        # All three are identical
        return True
        
    return False
