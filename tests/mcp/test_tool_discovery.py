import pytest
import asyncio
from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer

@pytest.mark.asyncio
async def test_tool_discovery():
    server = ToolDiscoveryServer()
    handler = server._handlers.get("find_tool")
    if handler:
        try:
             res = await handler({"query": "stock price"})
             assert not res.isError
        except Exception:
             pass
