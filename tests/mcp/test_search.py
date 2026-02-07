import pytest
import asyncio
from mcp_servers.search_server.server import SearchServer

@pytest.mark.asyncio
async def test_search_server():
    server = SearchServer()
    tools = server.get_tools()
    assert len(tools) > 0, "SearchServer has no tools"
