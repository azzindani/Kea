import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_google_search_server():
    """Verify Google Search Server executes using MCP Client."""
    
    params = get_server_params("google_search_server", extra_dependencies=["googlesearch-python", "beautifulsoup4"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "search_google" in tool_names
            assert "find_pdf" in tool_names
            
            print("Google Search verification passed (Tools present).")
