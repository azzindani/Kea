import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_crawler_server():
    """Verify Crawler Server executes using MCP Client."""
    
    # Crawler server dependencies - assuming generic for now as none specified in FastMCP
    # Check if 'crawl4ai' or 'beautifulsoup4' is needed. 
    # Based on tools names (crawl_ops), it likely needs something.
    # Safe bet: beautifulsoup4, requests, maybe crawl4ai if used.
    # Let's try minimal first.
    params = get_server_params("crawler_server", extra_dependencies=["beautifulsoup4", "requests"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "web_crawler" in tool_names
            assert "sitemap_parser" in tool_names
            
            print("Crawler verification passed (Tools present).")
