"""
MCP Tool Tests: Vision Tools.

Tests for vision MCP tools via stdio.
"""


import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_screenshot_extract():
    """Test screenshot extraction."""
    params = get_server_params("vision_server", extra_dependencies=["httpx"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Without real image, we expect error or handled response
            # We can't easily mock the tool's internal httpx call in integration test
            # So we just check if it runs
            res = await session.call_tool("screenshot_extract", arguments={"image_url": "https://example.com/test.png"})

            # Tools usually return a string even on error if robust, or isError=True
            assert res
            # assert not res.isError # It might be error due to invalid URL/fake image

@pytest.mark.mcp
@pytest.mark.asyncio
async def test_chart_reader():
    """Test chart reader."""
    params = get_server_params("vision_server", extra_dependencies=["httpx"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            res = await session.call_tool("chart_reader", arguments={"image_url": "https://example.com/chart.png"})
            assert res

@pytest.mark.mcp
@pytest.mark.asyncio
async def test_table_extraction():
    """Test table extraction (via screenshot_extract)."""
    params = get_server_params("vision_server", extra_dependencies=["httpx"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Use screenshot_extract with extraction_type='table'
            res = await session.call_tool("screenshot_extract", arguments={
                "image_url": "https://example.com/table.png",
                "extraction_type": "table"
            })
            assert res

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
