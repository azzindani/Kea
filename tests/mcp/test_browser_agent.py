import pytest
import asyncio
from mcp_servers.browser_agent_server.server import BrowserAgentServer

@pytest.mark.asyncio
async def test_browser_agent():
    server = BrowserAgentServer()
    # No functional test possible without GUI/Network usually
    assert len(server.get_tools()) > 0
