"""
MCP Server Tests.

Tests for all MCP tool servers.
"""

import pytest
import asyncio

from shared.mcp.protocol import ToolResult, TextContent


# ============================================================================
# Scraper Server Tests
# ============================================================================

class TestScraperServer:
    """Tests for the scraper MCP server."""
    
    @pytest.mark.asyncio
    async def test_fetch_url_success(self):
        """Test successful URL fetch."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({"url": "https://example.com"})
        
        assert not result.isError
        assert len(result.content) > 0
        assert "Example Domain" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_fetch_url_missing_url(self):
        """Test fetch_url with missing URL."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({})
        
        assert result.isError
        assert "required" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_url_invalid_url(self):
        """Test fetch_url with invalid URL."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        result = await fetch_url_tool({"url": "https://invalid.domain.that.does.not.exist.xyz"})
        
        assert result.isError


# ============================================================================
# Python Server Tests
# ============================================================================

class TestPythonServer:
    """Tests for the Python MCP server."""
    
    @pytest.mark.asyncio
    async def test_execute_code_basic(self):
        """Test basic code execution."""
        from mcp_servers.python_server.tools.execute_code import execute_code_tool
        
        result = await execute_code_tool({"code": "print(2 + 2)"})
        
        assert not result.isError
        assert "4" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_execute_code_with_pandas(self):
        """Test code execution with pandas."""
        from mcp_servers.python_server.tools.execute_code import execute_code_tool
        
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df.sum())
"""
        result = await execute_code_tool({"code": code})
        
        assert not result.isError
    
    @pytest.mark.asyncio
    async def test_execute_code_forbidden(self):
        """Test that forbidden operations are blocked."""
        from mcp_servers.python_server.tools.execute_code import execute_code_tool
        
        result = await execute_code_tool({"code": "import os; os.system('ls')"})
        
        assert result.isError
        assert "forbidden" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_sql_query_basic(self):
        """Test basic SQL query."""
        from mcp_servers.python_server.tools.sql_query import sql_query_tool
        
        result = await sql_query_tool({
            "query": "SELECT 1 + 1 as result",
        })
        
        assert not result.isError
        assert "2" in result.content[0].text


# ============================================================================
# Search Server Tests
# ============================================================================

class TestSearchServer:
    """Tests for the search MCP server."""
    
    @pytest.mark.asyncio
    async def test_web_search_basic(self):
        """Test basic web search."""
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        result = await web_search_tool({"query": "python programming"})
        
        assert not result.isError
        assert "Results" in result.content[0].text or "python" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_web_search_missing_query(self):
        """Test search with missing query."""
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        result = await web_search_tool({})
        
        assert result.isError


# ============================================================================
# Analysis Server Tests
# ============================================================================

class TestAnalysisServer:
    """Tests for the analysis MCP server."""
    
    @pytest.mark.asyncio
    async def test_meta_analysis_basic(self):
        """Test basic meta-analysis."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "A", "value": 100},
                {"source": "B", "value": 110},
                {"source": "C", "value": 105},
            ],
            "analysis_type": "comparison"
        })
        
        assert not result.isError
        assert "Mean" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_trend_detection_basic(self):
        """Test basic trend detection."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_trend_detection({
            "data": [10, 12, 15, 18, 22, 25, 30],
            "metric_name": "Growth"
        })
        
        assert not result.isError
        assert "Increasing" in result.content[0].text


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
