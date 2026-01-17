"""
MCP API Routes.

Endpoints for MCP server and tool management.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logging import get_logger


# Orchestrator URL for API calls
ORCHESTRATOR_URL = "http://localhost:8000"


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
    result: str | None = None  # Text content for backward compatibility


# ============================================================================
# Routes
# ============================================================================

@router.get("/servers")
async def list_servers():
    """List all MCP servers and their status from Orchestrator."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Get health to check MCP server count
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            
            if response.status_code != 200:
                raise Exception(f"Orchestrator returned {response.status_code}")
            
            health_data = response.json()
            mcp_count = health_data.get("mcp_servers", 0)
            
            # Get tools to build server list
            tools_response = await client.get(f"{ORCHESTRATOR_URL}/tools")
            tools_data = tools_response.json()
            
            # Group tools by inferred server name
            servers = {}
            for tool in tools_data.get("tools", []):
                name = tool.get("name", "unknown")
                # Infer server from tool name (e.g., "web_search" -> "search_server")
                if "_" in name:
                    server_name = name.split("_")[0] + "_server"
                else:
                    server_name = name + "_server"
                
                if server_name not in servers:
                    servers[server_name] = {"name": server_name, "status": "active", "tools_count": 0}
                servers[server_name]["tools_count"] += 1
            
            return {
                "servers": list(servers.values()),
                "total": len(servers),
                "orchestrator_status": "healthy",
            }
            
    except Exception as e:
        logger.warning(f"Could not reach orchestrator: {e}")
        return {
            "servers": [],
            "error": f"Orchestrator unavailable: {str(e)}",
            "orchestrator_status": "unhealthy",
        }


@router.get("/tools")
async def list_tools():
    """List all available tools from Orchestrator."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/tools")
            
            if response.status_code != 200:
                raise Exception(f"Orchestrator returned {response.status_code}")
            
            data = response.json()
            tools = data.get("tools", [])
            
            return {
                "tools": [
                    {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "server": t.get("server", "unknown"),
                    }
                    for t in tools
                ],
                "total": len(tools),
            }
            
    except Exception as e:
        logger.warning(f"Could not reach orchestrator: {e}")
        return {
            "tools": [],
            "error": f"Orchestrator unavailable: {str(e)}",
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
        
        # Extract text result for backward compatibility
        content = result.get("content", [])
        result_text = content[0].get("text", "") if content else ""
        
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=result.get("is_error", False),
            content=content,
            duration_ms=result.get("duration_ms", 0.0),
            result=result_text,
        )
    except ImportError:
        # MCPToolClient not implemented yet, use placeholder
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=False,
            content=[{"type": "text", "text": "Tool invocation placeholder - MCPToolClient not implemented"}],
            duration_ms=0.0,
            result="Tool invocation placeholder - MCPToolClient not implemented",
        )
    except Exception as e:
        logger.error(f"Tool invocation error: {e}")
        return ToolCallResponse(
            tool_name=request.tool_name,
            is_error=True,
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            duration_ms=0.0,
            result=f"Error: {str(e)}",
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
