import pytest
import asyncio

try:
    from mcp_servers.textblob_server.server import TextBlobServer
except ImportError:
    pytest.skip("TextBlob dependencies missing", allow_module_level=True)

@pytest.mark.asyncio
async def test_textblob_sentiment():
    server = TextBlobServer()
    handler = server._handlers.get("analyze_sentiment")
    if handler:
        res = await handler({"text": "I love this product!"})
        assert not res.isError
        assert "polarity" in res.content[0].text
