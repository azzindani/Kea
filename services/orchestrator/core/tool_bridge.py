"""
REST-Based Tool Executor Bridge.

Bridges the KernelCell's tool_executor interface to the MCP Host service
via HTTP REST. Respects microservice boundaries — NO imports from
services.mcp_host.

The bridge provides:
1. Tool execution: POST /tools/execute
2. Batch execution: POST /tools/batch
3. Tool discovery: GET /tools
4. LLM-based parameter correction on failure
5. Configurable retry with exponential backoff

Usage:
    executor = create_tool_executor()
    result = await executor("web_search", {"query": "AI market size"})
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from shared.logging import get_logger
from shared.prompts import get_agent_prompt, get_kernel_config
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)

# Load retry config once
_RETRY_CFG: dict = get_kernel_config("retry") or {}
_BASE_RETRIES: int = _RETRY_CFG.get("base_retries", 5)
_LLM_CALLBACKS_CFG: dict = get_kernel_config("llm_callbacks") or {}
_PLANNER_TEMP: float = _LLM_CALLBACKS_CFG.get("planner_temperature", 0.3)
_PLANNER_MAX_TOKENS: int = _LLM_CALLBACKS_CFG.get("planner_max_tokens", 32768)


async def _llm_correct_parameters(
    query: str,
    tool_name: str,
    failed_arguments: dict,
    error_message: str,
    tool_schema: dict | None = None,
) -> dict | None:
    """
    Use LLM to intelligently correct tool parameters after failure.

    Returns corrected arguments dict, or None if correction is not possible.
    """
    import os
    import re

    if not os.getenv("OPENROUTER_API_KEY"):
        return None

    try:
        from shared.config import get_settings
        from shared.llm import LLMConfig, OpenRouterProvider
        from shared.llm.provider import LLMMessage, LLMRole

        provider = OpenRouterProvider()
        config = LLMConfig(
            model=get_settings().models.planner_model,
            temperature=_PLANNER_TEMP,
            max_tokens=_PLANNER_MAX_TOKENS,
        )

        schema_info = ""
        if tool_schema:
            schema_info = f"\n**Tool Schema:** {json.dumps(tool_schema, indent=2)}"

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=get_agent_prompt("parameter_corrector"),
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=(
                    f"A tool execution failed. Analyze and suggest parameter corrections:\n\n"
                    f"**User Query:** {query}\n"
                    f"**Tool Name:** {tool_name}\n"
                    f"**Arguments That Failed:** {json.dumps(failed_arguments, indent=2)}\n"
                    f"**Error Message:** {error_message}{schema_info}\n\n"
                    "Based on the error, what are the CORRECT parameters?\n"
                    "Return JSON only, matching the parameter names from failed arguments."
                ),
            ),
        ]

        response = await provider.complete(messages, config)
        content = response.content.strip()

        json_match = re.search(r"\{[^}]+\}", content)
        if json_match:
            corrected = json.loads(json_match.group(0))
            if corrected:
                return corrected

    except Exception as e:
        logger.error(f"LLM parameter correction failed: {e}")

    return None


def create_tool_executor(
    query: str = "",
    timeout: float = 30.0,
    max_retries: int | None = None,
) -> Callable[[str, dict], Awaitable[Any]]:
    """
    Create a tool executor that calls MCP Host via REST API.

    Args:
        query: Original user query (used for LLM parameter correction context).
        timeout: HTTP timeout in seconds.
        max_retries: Max retries on failure. Defaults to kernel.yaml retry config.

    Returns:
        Async callable: (tool_name: str, arguments: dict) -> str
    """
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    retries = max_retries if max_retries is not None else _BASE_RETRIES

    # Deduplication cache (per-executor instance)
    completed_calls: dict[str, str] = {}

    async def execute_tool(name: str, args: dict) -> str:
        """Execute a tool via MCP Host REST API with retry and self-correction."""
        # Deduplication
        args_str = json.dumps(args, sort_keys=True, default=str)
        call_hash = hashlib.md5(f"{name}:{args_str}".encode()).hexdigest()

        if call_hash in completed_calls:
            logger.info(f"Tool bridge: dedup skip {name}")
            return completed_calls[call_hash]

        current_args = args.copy()
        last_error = ""

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        f"{mcp_url}/tools/execute",
                        json={"tool_name": name, "arguments": current_args},
                    )

                if resp.status_code == 404:
                    return f"ERROR: Tool {name} not found"

                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    if attempt < retries:
                        logger.warning(
                            f"Tool bridge: {name} HTTP error (attempt {attempt + 1}/"
                            f"{retries + 1}): {last_error[:100]}"
                        )
                        await asyncio.sleep(min(2**attempt, 8))
                        continue
                    return f"ERROR: {last_error}"

                data = resp.json()

                # Extract text content from ToolResponse
                output = data.get("output", {})
                text = output.get("text", "")
                is_error = data.get("is_error", False)

                if is_error and attempt < retries:
                    error_text = text or output.get("error", "Unknown error")
                    logger.warning(
                        f"Tool bridge: {name} returned error (attempt {attempt + 1}/"
                        f"{retries + 1}): {error_text[:100]}"
                    )

                    # Try LLM correction
                    corrected = await _llm_correct_parameters(
                        query=query,
                        tool_name=name,
                        failed_arguments=current_args,
                        error_message=error_text[:500],
                    )
                    if corrected:
                        logger.info(f"Tool bridge: LLM corrected args for {name}")
                        current_args = corrected
                        continue

                    # No correction possible, return what we have
                    break

                # Success or final attempt
                result = text or json.dumps(output, default=str)
                completed_calls[call_hash] = result
                return result

            except httpx.TimeoutException:
                last_error = f"Timeout after {timeout}s"
                if attempt < retries:
                    logger.warning(
                        f"Tool bridge: {name} timeout (attempt {attempt + 1}/{retries + 1})"
                    )
                    await asyncio.sleep(min(2**attempt, 8))
                    continue

            except httpx.ConnectError:
                last_error = f"Cannot connect to MCP Host at {mcp_url}"
                if attempt < retries:
                    logger.warning(
                        f"Tool bridge: connection error (attempt {attempt + 1}/{retries + 1})"
                    )
                    await asyncio.sleep(min(2**attempt, 8))
                    continue

            except Exception as e:
                last_error = str(e)
                if attempt < retries:
                    logger.warning(
                        f"Tool bridge: {name} error (attempt {attempt + 1}/{retries + 1}): {e}"
                    )
                    await asyncio.sleep(min(2**attempt, 8))
                    continue

        return f"ERROR: {name} failed after {retries + 1} attempts: {last_error}"

    return execute_tool


async def discover_tools(
    timeout: float = 10.0,
    query: str | None = None,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    Discover tools from MCP Host, optimized for Just-In-Time (JIT) loading.
    
    If `query` or `domain` is provided, it consults `tool_registry.yaml` to
    identify relevant servers and *only* wakes those up.
    Otherwise, it performs a full scan (which wakes all servers).
    """
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    
    # 1. Identify Target Servers (JIT Optimization)
    target_servers = set()
    
    if query:
        try:
            # Load registry map: keywords -> server
            from pathlib import Path
            import yaml
            
            # Find configs/ relative to this file
            # services/orchestrator/core/tool_bridge.py -> ... -> Kea/configs
            try:
                root_path = Path(__file__).resolve().parents[3]
                registry_path = root_path / "configs" / "tool_registry.yaml"
            except IndexError:
                registry_path = Path("configs/tool_registry.yaml")

            if registry_path and registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    reg_data = yaml.safe_load(f)
                    
                items = reg_data.get("items", {})
                query_lower = query.lower()
                
                for tool_key, tool_cfg in items.items():
                    # Check keywords
                    keywords = tool_cfg.get("keywords", [])
                    if any(k in query_lower for k in keywords):
                        target_servers.add(tool_cfg.get("server"))
                        
                    # Also check tool name itself
                    if tool_key in query_lower:
                        target_servers.add(tool_cfg.get("server"))
        except Exception as e:
            logger.warning(f"JIT Registry lookup failed: {e}")

    # Always include 'mcp_host' (system tools) and domain-specific defaults
    if not target_servers:
        # Fallback 1: If domain implies a specifc server
        if domain == "finance":
            target_servers.add("yfinance_server")
        elif domain == "crypto":
            target_servers.add("ccxt_server")
        elif domain == "academic":
            target_servers.add("academic_server")
        elif domain == "coding":
            target_servers.add("python_server")
            
        # Fallback 2: General purpose
        target_servers.add("search_server")
        target_servers.add("browser_agent_server")

    # 2. Fetch tools from targets
    discovered_tools = []
    
    async def _fetch_server(srv_name: str):
        if not srv_name: return
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Use new 'server=' param to avoid waking everything
                resp = await client.get(f"{mcp_url}/tools", params={"server": srv_name})
                if resp.status_code == 200:
                    data = resp.json()
                    tools = data.get("tools", [])
                    logger.info(f"JIT loaded {len(tools)} tools from {srv_name}")
                    return tools
        except Exception:
            pass # Server might be down or name wrong, ignore
        return []

    # Parallel fetch
    results = await asyncio.gather(*[_fetch_server(s) for s in target_servers if s])
    for r in results:
        if r:
            discovered_tools.extend(r)
            
    # If JIT failed to find anything useful, fallback to full scan (safety net)
    if not discovered_tools and not query:
        logger.warning("JIT discovery found no tools, falling back to full scan")
        try:
            async with httpx.AsyncClient(timeout=timeout*2) as client:
                resp = await client.get(f"{mcp_url}/tools") # No server param = all
                if resp.status_code == 200:
                    return resp.json().get("tools", [])
        except Exception as e:
            logger.warning(f"Full tool discovery failed: {e}")

    return discovered_tools


async def verify_mcp_connectivity(timeout: float = 3.0) -> bool:
    """Check if MCP Host is reachable."""
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{mcp_url}/health")
            return resp.status_code == 200
    except Exception:
        return False
