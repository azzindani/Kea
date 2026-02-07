import pytest
import asyncio
from mcp_servers.ddg_search_server.server import DdgSearchServer

@pytest.mark.asyncio
async def test_ddg_search():
    server = DdgSearchServer()
    assert "search" in server._handlers
