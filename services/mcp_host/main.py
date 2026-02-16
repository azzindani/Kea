from fastapi import FastAPI, HTTPException
import fastapi
import uvicorn
from contextlib import asynccontextmanager

from shared.logging import get_logger
from services.mcp_host.core.models import (
    ToolRequest,
    BatchToolRequest,
    ToolResponse,
    ToolSearchRequest,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Registry & Supervisor
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    
    # Static RAG Population (Background)
    # Ensure MCP Host also populates the registry for standard API usage
    import asyncio
    asyncio.create_task(registry.register_discovered_tools())
    
    # Start the Supervisor (The Factory Manager)
    from services.mcp_host.core.supervisor_engine import get_supervisor
    supervisor = get_supervisor()
    await supervisor.start()
    
    yield
    # Shutdown: Stop servers
    await registry.shutdown()


app = FastAPI(title="MCP Host", lifespan=lifespan)


@app.get("/health")
async def health():
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    count = len(registry.server_configs)
    
    return {
        "status": "ok", 
        "service": "mcp_host",
        "servers_available": count,
        "active_sessions": len(registry.active_sessions)
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
        from shared.schemas import ToolOutput
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
    from shared.schemas import ToolOutput
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


@app.post("/tools/dispatch")
async def dispatch_batch(
    request: BatchToolRequest, 
    background_tasks: fastapi.BackgroundTasks
):
    """
    Fire-and-Forget Dispatcher (Parallel Micro-Tasks).
    Returns immediately with batch_id.
    """
    from shared.dispatcher import get_dispatcher
    from services.mcp_host.core.background import run_swarm_batch
    
    dispatcher = get_dispatcher()
    
    # Convert request models to dicts
    tasks_data = [
        {"tool_name": t.tool_name, "arguments": t.arguments} 
        for t in request.tasks
    ]
    
    # 1. Create Batch in DB
    batch_id = await dispatcher.create_batch(tasks_data)
    
    # 2. Fire Background Swarm
    background_tasks.add_task(run_swarm_batch, batch_id, tasks_data)
    
    return {
        "status": "batch_started",
        "batch_id": batch_id,
        "message": f"Started {len(tasks_data)} tasks. Use check_batch_status('{batch_id}') to monitor."
    }


@app.get("/tools/batch/{batch_id}")
async def check_batch(batch_id: str):
    """Check status of a dispatched batch."""
    from shared.dispatcher import get_dispatcher
    dispatcher = get_dispatcher()
    try:
        status = await dispatcher.get_batch_status(batch_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) # Port 8002 (MCP Host)
