"""
Unit Tests: Search Tools.

Tests for mcp_servers/search_server/tools/*.py
"""

import pytest


class TestWebSearchTool:
    """Tests for web_search tool."""
    
    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Basic web search."""
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        result = await web_search_tool({
            "query": "python programming",
            "max_results": 3,
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_domain(self):
        """Search with domain filter."""
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        result = await web_search_tool({
            "query": "documentation",
            "max_results": 5,
            "domain": "python.org",
        })
        
        assert result is not None


class TestNewsSearchTool:
    """Tests for news_search tool."""
    
    @pytest.mark.asyncio
    async def test_news_search(self):
        """Search recent news."""
        from mcp_servers.search_server.tools.news_search import news_search_tool
        
        result = await news_search_tool({
            "query": "technology",
            "days": 7,
            "max_results": 5,
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_news_specific_topic(self):
        """Search news for specific topic."""
        from mcp_servers.search_server.tools.news_search import news_search_tool
        
        result = await news_search_tool({
            "query": "artificial intelligence",
            "days": 3,
        })
        
        assert result is not None


class TestAcademicSearchTool:
    """Tests for academic_search tool."""
    
    @pytest.mark.asyncio
    async def test_arxiv_search(self):
        """Search arXiv papers."""
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        result = await academic_search_tool({
            "query": "machine learning",
            "max_results": 3,
            "source": "arxiv",
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_semantic_scholar_search(self):
        """Search Semantic Scholar."""
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        result = await academic_search_tool({
            "query": "neural networks",
            "max_results": 3,
            "source": "semantic_scholar",
        })
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
