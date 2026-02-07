import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_newspaper_server():
    """Verify Newspaper Server executes using MCP Client."""
    params = get_server_params("newspaper_server", extra_dependencies=["newspaper3k", "lxml", "lxml_html_clean"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            tool_names = [t.name for t in tools]
            assert "get_article_text" in tool_names
            print("Newspaper verification passed (Tools present).")
