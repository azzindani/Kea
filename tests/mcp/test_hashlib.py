import pytest
import asyncio
import hashlib
from mcp_servers.hashlib_server.server import HashlibServer

@pytest.mark.asyncio
async def test_hashing():
    server = HashlibServer()
    handler = server._handlers.get("calculate_hash")
    if handler:
        text = "Hello World"
        expected = hashlib.sha256(text.encode()).hexdigest()
        res = await handler({"text": text, "algorithm": "sha256"})
        assert not res.isError
        assert expected in res.content[0].text
