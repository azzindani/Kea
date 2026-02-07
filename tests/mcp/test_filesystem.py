import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_filesystem_server():
    """Verify Filesystem Server executes using MCP Client."""
    
    params = get_server_params("filesystem_server", extra_dependencies=["asyncpg"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "fs_ls" in tool_names or "list_directory" in tool_names # Supporting potential aliases
            
            print("Filesystem verification passed (Tools present).")
