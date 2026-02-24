"""
MCP Tool Tests: Search Tools.

Tests for search MCP tools via stdio.
"""


import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_web_search_basic():
    """Perform basic web search."""
    params = get_server_params("search_server")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Mock or Real? For now we expect the tool to handle real requests or fail gracefully
            # If no API key, it returns error string, which is fine, we just check tool execution
            res = await session.call_tool("web_search", arguments={"query": "python programming", "max_results": 1})

            # We don't assert validity of search results (network dep), just that tool runs
            assert not res.isError
            assert res.content
            assert len(res.content) > 0

@pytest.mark.mcp
@pytest.mark.asyncio
async def test_news_search_query():
    """Search for news."""
    params = get_server_params("search_server")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            res = await session.call_tool("news_search", arguments={"query": "technology", "days": 1, "max_results": 1})

            assert not res.isError
            assert res.content

@pytest.mark.mcp
@pytest.mark.asyncio
async def test_arxiv_search():
    """Search academic papers (via academic_server)."""
    # Note: academic_search tool is named 'arxiv_search' in academic_server
    params = get_server_params("academic_server", extra_dependencies=["httpx", "arxiv"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            res = await session.call_tool("arxiv_search", arguments={"query": "machine learning", "max_results": 1})

            assert not res.isError
            assert res.content

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
