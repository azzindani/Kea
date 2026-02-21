"""
MCP API Routes.

Endpoints for MCP server and tool management.
Updated to use MCP Host microservice client in v0.4.0.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from shared.logging.main import get_logger
from services.api_gateway.clients.mcp_client import MCPClient, get_mcp_client


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ToolCallRequest(BaseModel):
    """Tool call request."""
    tool_name: str
    arguments: dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """Tool call response."""
    tool_name: str
    is_error: bool
    content: list[dict]
    duration_ms: float
    result: str | None = None


# ============================================================================
# Routes
# ============================================================================

@router.get("/tools")
async def list_tools(client: MCPClient = Depends(get_mcp_client)):
    """List all available tools from MCP Host."""
    try:
        tools = await client.list_tools()
        return {
            "tools": tools,
            "total": len(tools),
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=503, detail=f"MCP Host unavailable: {str(e)}")


@router.get("/search")
async def search_tools(query: str, limit: int = 5, client: MCPClient = Depends(get_mcp_client)):
    """Search for tools via RAG on MCP Host."""
    try:
        tools = await client.search_tools(query, limit)
        return {
            "tools": tools,
            "total": len(tools),
        }
    except Exception as e:
        logger.error(f"Failed to search tools: {e}")
        raise HTTPException(status_code=503, detail=f"MCP Host unavailable: {str(e)}")


@router.post("/invoke", response_model=ToolCallResponse)
async def invoke_tool(request: ToolCallRequest, client: MCPClient = Depends(get_mcp_client)):
    """
    Invoke a tool via MCP Host.
    """
    logger.info(f"Invoking tool: {request.tool_name}")
    
    try:
        result = await client.invoke(request.tool_name, request.arguments)
        
        # result is ToolResponse from mcp-host
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=result.get("is_error", False),
            content=result.get("content", []),
            duration_ms=result.get("duration_ms", 0.0),
            result=result.get("result", ""),
        )
    except Exception as e:
        logger.error(f"Tool invocation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/invoke", response_model=ToolCallResponse)
async def invoke_tool_alias(request: ToolCallRequest, client: MCPClient = Depends(get_mcp_client)):
    """Alias for /invoke."""
    return await invoke_tool(request, client)
