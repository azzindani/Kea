"""
MCP Tool Tests: Search Tools.

Tests for search MCP tools via API.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestWebSearch:
    """Tests for web_search tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Perform basic web search."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "web_search",
                    "arguments": {
                        "query": "python programming",
                        "max_results": 5,
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


class TestNewsSearch:
    """Tests for news_search tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_news_query(self):
        """Search for news."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "news_search",
                    "arguments": {
                        "query": "technology news",
                        "days": 7,
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


class TestAcademicSearch:
    """Tests for academic_search tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_arxiv_search(self):
        """Search academic papers."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "academic_search",
                    "arguments": {
                        "query": "machine learning",
                        "max_results": 5,
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])
