import pytest
import asyncio
from mcp_servers.finta_server.server import FintaServer

@pytest.mark.asyncio
async def test_minimal():
    server = FintaServer()
    tools = server.get_tools()
    assert len(tools) > 0
