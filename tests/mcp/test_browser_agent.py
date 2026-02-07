import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_browser_agent():
    """Verify Browser Agent executes using MCP Client."""
    
    # Needs browser-use and playwright usually, but standard test just checks tool presence
    # We skip browser interaction unless running full simulation
    params = get_server_params("browser_agent_server", extra_dependencies=["browser-use", "playwright"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "open_tab" in tool_names or "multi_site_browse" in tool_names
            
            print("Browser Agent verification passed (Tools present).")
