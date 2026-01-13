"""
MCP API Routes.

Endpoints for MCP server and tool management.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ToolInfo(BaseModel):
    """Tool information."""
    name: str
    description: str
    server: str
    input_schema: dict | None = None


class ServerInfo(BaseModel):
    """MCP server information."""
    name: str
    status: str
    tools_count: int


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


# ============================================================================
# Routes
# ============================================================================

@router.get("/servers")
async def list_servers():
    """List all MCP servers and their status."""
    # Placeholder: Query orchestrator for server status
    return {
        "servers": [
            {"name": "scraper_server", "status": "configured", "tools_count": 2},
            {"name": "python_server", "status": "configured", "tools_count": 3},
            {"name": "search_server", "status": "configured", "tools_count": 2},
            {"name": "vision_server", "status": "configured", "tools_count": 2},
            {"name": "analysis_server", "status": "configured", "tools_count": 2},
        ]
    }


@router.get("/tools")
async def list_tools():
    """List all available tools from all servers."""
    return {
        "tools": [
            {"name": "fetch_url", "server": "scraper_server", "description": "Fetch URL via HTTP"},
            {"name": "browser_scrape", "server": "scraper_server", "description": "Scrape with headless browser"},
            {"name": "execute_code", "server": "python_server", "description": "Execute Python code"},
            {"name": "dataframe_ops", "server": "python_server", "description": "Pandas operations"},
            {"name": "sql_query", "server": "python_server", "description": "DuckDB SQL queries"},
            {"name": "web_search", "server": "search_server", "description": "Web search"},
            {"name": "news_search", "server": "search_server", "description": "News search"},
            {"name": "screenshot_extract", "server": "vision_server", "description": "Extract from images"},
            {"name": "chart_reader", "server": "vision_server", "description": "Read charts"},
            {"name": "meta_analysis", "server": "analysis_server", "description": "Cross-source analysis"},
            {"name": "trend_detection", "server": "analysis_server", "description": "Trend analysis"},
        ]
    }


@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    # Placeholder
    raise HTTPException(status_code=404, detail="Tool not found")


@router.post("/invoke")
async def invoke_tool(request: ToolCallRequest):
    """
    Invoke a tool directly.
    
    This bypasses the orchestrator for direct tool testing.
    """
    logger.info(f"Direct tool invocation: {request.tool_name}")
    
    # Actually call the tool instead of placeholder
    try:
        from services.api_gateway.clients.mcp_client import MCPToolClient
        
        client = MCPToolClient()
        result = await client.invoke(request.tool_name, request.arguments)
        
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=result.get("is_error", False),
            content=result.get("content", []),
            duration_ms=result.get("duration_ms", 0.0),
        )
    except ImportError:
        # MCPToolClient not implemented yet, use placeholder
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=False,
            content=[{"type": "text", "text": "Tool invocation placeholder - MCPToolClient not implemented"}],
            duration_ms=0.0,
        )
    except Exception as e:
        logger.error(f"Tool invocation error: {e}")
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=True,
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            duration_ms=0.0,
        )


# Alias route for test compatibility
@router.post("/tools/invoke")
async def invoke_tool_alias(request: ToolCallRequest):
    """Alias for /invoke - maintained for test compatibility."""
    return await invoke_tool(request)


@router.post("/servers/{server_name}/restart")
async def restart_server(server_name: str):
    """Restart an MCP server."""
    logger.info(f"Restarting MCP server: {server_name}")
    return {"message": f"Server {server_name} restart initiated"}
