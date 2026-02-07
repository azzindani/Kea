import pytest
import asyncio
from mcp_servers.shutil_server.server import ShutilServer

@pytest.mark.asyncio
async def test_shutil():
    server = ShutilServer()
    assert len(server.get_tools()) > 0
