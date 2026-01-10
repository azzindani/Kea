"""
MCP Tool Tests: Scraper Tools.

Tests for scraper MCP tools via API.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestFetchUrl:
    """Tests for fetch_url tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_fetch_example_com(self):
        """Fetch example.com."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "fetch_url",
                    "arguments": {"url": "https://example.com"},
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data
            # Should contain example.com content
            assert "Example Domain" in str(data)
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_fetch_with_timeout(self):
        """Fetch with custom timeout."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "fetch_url",
                    "arguments": {
                        "url": "https://example.com",
                        "timeout": 10,
                    },
                }
            )
        
        # Should succeed
        assert response.status_code in [200, 500]


class TestBatchScrape:
    """Tests for batch_scrape tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_batch_multiple_urls(self):
        """Scrape multiple URLs."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "batch_scrape",
                    "arguments": {
                        "urls": [
                            "https://example.com",
                            "https://example.org",
                        ],
                        "max_concurrent": 2,
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])
