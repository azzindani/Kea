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
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check response structure
        assert "content" in data or "result" in data, f"Response missing content: {data}"
        assert data.get("is_error") == False, f"Tool returned error: {data}"
        
        # Check for actual content from example.com
        content_str = str(data.get("content", data.get("result", "")))
        assert "Example Domain" in content_str or "example" in content_str.lower(), \
            f"Expected example.com content, got: {content_str[:200]}"
    
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
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


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
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check response structure
        assert "content" in data or "result" in data, f"Response missing content: {data}"
        assert data.get("is_error") == False, f"Tool returned error: {data}"
        
        # Check for batch scrape results
        content_str = str(data.get("content", data.get("result", "")))
        assert "Batch" in content_str or "example" in content_str.lower(), \
            f"Expected batch results, got: {content_str[:200]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])

