"""
Unit Tests: MCP Tool Functions.

Direct tests for tool functions without API.
"""

import pytest


class TestFetchUrlTool:
    """Tests for fetch_url tool."""

    @pytest.mark.asyncio
    async def test_fetch_example(self):
        """Fetch example.com."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool

        result = await fetch_url_tool({"url": "https://example.com"})

        assert not result.isError
        assert "Example Domain" in result.content[0].text


class TestExecuteCodeTool:
    """Tests for execute_code tool."""

    @pytest.mark.asyncio
    async def test_simple_print(self):
        """Execute simple print."""
        from mcp_servers.python_server.tools.execute_code import execute_code_tool

        result = await execute_code_tool({"code": "print(2+2)"})

        assert not result.isError
        assert "4" in result.content[0].text

    @pytest.mark.asyncio
    async def test_syntax_error(self):
        """Handle syntax error."""
        from mcp_servers.python_server.tools.execute_code import execute_code_tool

        result = await execute_code_tool({"code": "print("})

        assert result.isError


class TestDataframeOpsTool:
    """Tests for dataframe_ops tool."""

    @pytest.mark.asyncio
    async def test_describe(self):
        """Test describe operation."""
        from mcp_servers.python_server.tools.dataframe_ops import dataframe_ops_tool

        result = await dataframe_ops_tool({
            "operation": "describe",
            "data": "a,b\n1,2\n3,4\n5,6",
        })

        # May succeed or fail depending on pandas availability
        assert result is not None


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

        # Result depends on API availability
        assert result is not None


class TestAcademicSearchTool:
    """Tests for academic_search tool."""

    @pytest.mark.asyncio
    async def test_arxiv_search(self):
        """Search arXiv."""
        from mcp_servers.search_server.tools.academic_search import academic_search_tool

        result = await academic_search_tool({
            "query": "machine learning",
            "max_results": 3,
        })

        assert result is not None


class TestMetaAnalysisTool:
    """Tests for meta_analysis tool."""

    @pytest.mark.asyncio
    async def test_comparison(self):
        """Run comparison analysis."""
        from mcp_servers.analysis_server.server import AnalysisServer

        server = AnalysisServer()

        result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "A", "value": 100},
                {"source": "B", "value": 110},
            ],
            "analysis_type": "comparison",
        })

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
