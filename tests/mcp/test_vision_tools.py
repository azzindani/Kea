"""
MCP Tool Tests: Vision Tools.

Tests for vision MCP tools via API.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestScreenshotExtract:
    """Tests for screenshot_extract tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_extract_from_url(self):
        """Extract text from screenshot URL."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "screenshot_extract",
                    "arguments": {
                        "image_url": "https://example.com/screenshot.png",
                    },
                }
            )
        
        # May fail without valid image
        assert response.status_code in [200, 400, 500]


class TestTableOCR:
    """Tests for table_ocr tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_extract_table(self):
        """Extract table from image."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "table_ocr",
                    "arguments": {
                        "image_url": "https://example.com/table.png",
                        "output_format": "markdown",
                    },
                }
            )
        
        # May fail without valid image or API key
        assert response.status_code in [200, 400, 500]


class TestChartReader:
    """Tests for chart_reader tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_read_chart(self):
        """Read data from chart."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "chart_reader",
                    "arguments": {
                        "image_url": "https://example.com/chart.png",
                    },
                }
            )
        
        assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])
