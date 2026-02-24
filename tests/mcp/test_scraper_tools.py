"""
MCP Tool Tests: Scraper Tools.

Tests for scraper MCP tools via API.
"""


import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_fetch_example_com():
    """Fetch example.com using stdio_client."""
    params = get_server_params("scraper_server", extra_dependencies=["playwright", "beautifulsoup4"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify tool exists
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            assert "fetch_url" in tool_names

            res = await session.call_tool("fetch_url", arguments={"url": "https://example.com"})
            content_str = res.content[0].text if res.content else ""
            if "ProxyError" in content_str or "RetryError" in content_str or "Connect" in content_str:
                skip_msg = "example.com unreachable (proxy/network restriction)"
            else:
                assert not res.isError
                assert "Example Domain" in content_str or "example" in content_str.lower()

    if "skip_msg" in locals():
        pytest.skip(skip_msg)

@pytest.mark.asyncio
async def test_fetch_with_timeout():
    """Fetch with custom timeout."""
    params = get_server_params("scraper_server", extra_dependencies=["playwright", "beautifulsoup4"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            res = await session.call_tool("fetch_url", arguments={"url": "https://example.com", "timeout": 10})
            content_str = res.content[0].text if res.content else ""
            if "ProxyError" in content_str or "RetryError" in content_str or "Connect" in content_str:
                skip_msg = "example.com unreachable (proxy/network restriction)"
            else:
                assert not res.isError
                assert "Example Domain" in content_str

    if "skip_msg" in locals():
        pytest.skip(skip_msg)

@pytest.mark.asyncio
async def test_batch_multiple_urls():
    """Scrape multiple URLs."""
    params = get_server_params("scraper_server", extra_dependencies=["playwright", "beautifulsoup4"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            urls = ["https://example.com", "https://example.org"]
            # batch_scrape might return text directly strictly or a JSON string, let's check implementation behavior through test
            # Assuming it returns a list of results in some format
            res = await session.call_tool("batch_scrape", arguments={"urls": urls, "max_concurrent": 2})
            content_str = res.content[0].text if res.content else ""
            if "ProxyError" in content_str or "RetryError" in content_str or "Connect" in content_str:
                skip_msg = "URLs unreachable (proxy/network restriction)"
            else:
                assert not res.isError
                assert "example" in content_str.lower()

    if "skip_msg" in locals():
        pytest.skip(skip_msg)

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
