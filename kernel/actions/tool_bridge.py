"""
REST-Based Tool Executor Bridge.

Bridges the KernelCell's tool_executor interface to the MCP Host service
via HTTP REST. Respects microservice boundaries   NO imports from
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
    timeout: float = 5.0,
    query: str = "",
    domain: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Discover relevant tools via RAG semantic search on the MCP Host.

    Replaces keyword YAML matching and hardcoded domain fallbacks with
    pgvector cosine-similarity search over all 2000+ registered tools
    across 60+ MCP servers.

    Args:
        timeout: HTTP timeout in seconds.
        query: Natural-language task description for semantic matching.
        domain: Optional domain hint prepended to query for better relevance.
        limit: Max tools to return (defaults to kernel_cell_explore config value).

    Returns:
        List of tool dicts with name, description, and inputSchema.
    """
    from shared.schemas import ToolSearchRequest

    if not query:
        return []

    cfg = get_kernel_config("kernel_cell_explore") or {}
    n_tools = limit or cfg.get("max_tools_to_scan", 15)

    # Prepend domain hint to improve semantic matching precision
    search_query = f"{domain}: {query}" if domain else query

    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    payload = ToolSearchRequest(query=search_query, limit=n_tools)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{mcp_url}/tools/search",
                json=payload.model_dump(),
            )
            if resp.status_code != 200:
                logger.warning(
                    f"Tool RAG search returned {resp.status_code}: {resp.text[:200]}"
                )
                return []
            tools = resp.json().get("tools", [])
            logger.info(f"Tool RAG search: {len(tools)} tools for query '{search_query[:60]}'")

            # Static fallback: when RAG returns 0 tools (cold start / empty registry)
            # fall back to GET /tools to give the LLM at least some tools to work with.
            if not tools:
                exec_cfg = get_kernel_config("kernel_cell_execute") or {}
                fallback_limit = exec_cfg.get("rag_fallback_static_limit", 0)
                if fallback_limit > 0:
                    logger.warning(
                        f"Tool RAG search returned 0 — static fallback (limit={fallback_limit})"
                    )
                    try:
                        async with httpx.AsyncClient(timeout=timeout) as client:
                            fb_resp = await client.get(f"{mcp_url}/tools")
                            if fb_resp.status_code == 200:
                                tools = fb_resp.json().get("tools", [])[:fallback_limit]
                                logger.info(
                                    f"Static fallback: {len(tools)} tools available"
                                )
                    except Exception as fe:
                        logger.warning(f"Static fallback failed: {fe}")

            return tools
    except httpx.TimeoutException:
        logger.warning("Tool RAG search timed out")
        return []
    except Exception as e:
        logger.warning(f"Tool RAG search failed: {e}")
        return []


async def verify_mcp_connectivity(timeout: float = 3.0) -> bool:
    """Check if MCP Host is reachable."""
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{mcp_url}/health")
            return resp.status_code == 200
    except Exception:
        return False
