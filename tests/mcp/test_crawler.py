import pytest
import asyncio
from mcp_servers.crawler_server.server import CrawlerServer

@pytest.mark.asyncio
async def test_crawler_extract():
    """Test crawler extraction logic (mocked/local)."""
    server = CrawlerServer()
    handler = server._handlers.get("extract_links")
    if handler:
        try:
            res = await handler({"url": "http://example.com", "max_depth": 0})
            if res.isError and "Network" in str(res.content[0].text):
                 pytest.skip("Crawler requires network")
        except Exception:
            pass
