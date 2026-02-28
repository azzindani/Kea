from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
import uvicorn
from prometheus_client import make_asgi_app
from contextlib import asynccontextmanager

from shared.logging.main import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
import asyncio
from shared.schemas import (
    ToolRequest, BatchToolRequest, ToolResponse, ToolSearchRequest, ToolOutput
)

# Initialize structured logging globally
# (Moved below settings loading)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: Initialize Registry
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    # Static RAG Population (Background)
    # Ensure MCP Host also populates the registry for standard API usage
    asyncio.create_task(registry.register_discovered_tools())
    
    yield
    # Shutdown: Stop servers
    await registry.shutdown()


from shared.config import get_settings
from shared.service_registry import ServiceRegistry, ServiceName

# Load settings
settings = get_settings()

setup_logging(LogConfig(
    level=settings.logging.level,
    service_name="mcp_host",
))

app = FastAPI(
    title=f"{settings.app.name} - MCP Host",
    version=settings.app.version,
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health():
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    count = len(registry.server_configs)
    
    return {
        "status": "ok", 
        "service": "mcp_host",
        "servers_available": count,
        "active_sessions": len(registry.active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/tools")
async def list_tools(server: str | None = None, limit: int | None = None):
    """List available tools, optionally filtered by server (JIT) or limited."""
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    if server:
        # JIT: Only list tools for this specific server
        tools = await registry.list_tools_for_server(server)
    else:
        # Full scan (legacy behavior, wakes all servers)
        tools = await registry.list_all_tools()
        
    if limit and limit > 0:
        tools = tools[:limit]
        
    return {"tools": tools}


@app.post("/tools/search")
async def search_tools(request: ToolSearchRequest):
    """
    Semantic tool search via pgvector RAG.

    Returns tools ranked by cosine similarity to the query — no hardcoded
    keywords or domain lists. Covers all 2000+ tools across 60+ MCP servers.
    """
    from services.mcp_host.core.session_registry import get_session_registry

    registry = get_session_registry()
    tools = await registry.search_tools(
        query=request.query, 
        limit=request.limit,
        min_similarity=request.min_similarity
    )
    return {"tools": tools}


@app.post("/tools/sync")
async def sync_tools(background: bool = True):
    """
    Triggers a full discovery and RAG registration of all MCP tools.
    """
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    if background:
        asyncio.create_task(registry.register_discovered_tools())
        return {"status": "sync_started", "detail": "Indexing in background"}
    else:
        await registry.register_discovered_tools()
        return {"status": "sync_complete"}


@app.post("/server/{server_name}/stop")
async def stop_server(server_name: str):
    """Stop a specific server to free resources."""
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    success = await registry.stop_server(server_name)
    if success:
        return {"status": "stopped", "server": server_name}
    else:
        return {"status": "not_running", "server": server_name}


@app.post("/tools/execute", response_model=ToolResponse)
async def execute_tool(request: ToolRequest):
    """Execute a single tool."""
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    try:
        # Find which server has this tool
        if not registry.tool_to_server:
            await registry.list_all_tools()
            
        server_name = registry.get_server_for_tool(request.tool_name)
        if not server_name:
            await registry.list_all_tools()
            server_name = registry.get_server_for_tool(request.tool_name)
            
        if not server_name:
            raise ValueError(f"Tool {request.tool_name} not found in any server")

        # Ephemeral Execution (Spawn -> Run -> Stop)
        result = await registry.execute_tool_ephemeral(
            server_name, 
            request.tool_name, 
            request.arguments
        )
        
        return ToolResponse.from_mcp_result(request.tool_name, result)
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return ToolResponse(
            tool_name=request.tool_name,
            output=ToolOutput(
                tool_name=request.tool_name,
                text=str(e),
                error=str(e),
                success=False
            ),
            is_error=True
        )


@app.post("/tools/batch", response_model=list[ToolResponse])
async def execute_batch(request: BatchToolRequest):
    """
    Execute multiple tools in parallel (Fan-Out).
    """
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    # We can't use registry directly for parallel calls efficiently unless we implement `call_tools_parallel`
    # or just use asyncio.gather here using sessions.
    
    async def _exec_one(task):
        try:
            # Re-implement lookup logic or reuse execute_tool logic?
            # Reuse logic for simplicity
            if not registry.tool_to_server:
                await registry.list_all_tools()
            server_name = registry.get_server_for_tool(task.tool_name)
            if not server_name:
                await registry.list_all_tools()
                server_name = registry.get_server_for_tool(task.tool_name)
            
            if not server_name:
                raise ValueError(f"Tool {task.tool_name} not found")
                
            # Ephemeral Execution
            res = await registry.execute_tool_ephemeral(
                server_name, 
                task.tool_name, 
                task.arguments
            )
            return ToolResponse.from_mcp_result(task.tool_name, res)
        except Exception as e:
            return ToolResponse(
                tool_name=task.tool_name,
                output=ToolOutput(
                    tool_name=task.tool_name,
                    text=str(e),
                    error=str(e),
                    success=False
                ),
                is_error=True
            )

    tasks = [_exec_one(t) for t in request.tasks]
    return await asyncio.gather(*tasks)


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=settings.api.host, 
        port=ServiceRegistry.get_port(ServiceName.MCP_HOST)
    )
