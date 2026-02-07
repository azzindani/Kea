import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_finviz_server():
    """Verify Finviz Server executes using MCP Client."""
    params = get_server_params("finviz_server", extra_dependencies=["finviz"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            tool_names = [t.name for t in tools]
            assert len(tools) > 0
            print("Finviz verification passed (Tools present).")
