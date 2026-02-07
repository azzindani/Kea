import pytest
import asyncio
from mcp_servers.bs4_server.server import Bs4Server

@pytest.mark.asyncio
async def test_bs4_parse():
    server = Bs4Server()
    handler = server._handlers.get("extract_text")
    if handler:
        html = "<html><body><p>Hello World</p></body></html>"
        res = await handler({"html_content": html})
        assert not res.isError
        assert "Hello World" in res.content[0].text
