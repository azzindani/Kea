import pytest
import asyncio
from mcp_servers.google_search_server.server import GoogleSearchServer

@pytest.mark.asyncio
async def test_google_search():
    server = GoogleSearchServer()
    assert len(server.get_tools()) > 0
