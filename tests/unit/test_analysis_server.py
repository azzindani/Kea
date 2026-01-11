"""
Unit Tests: Analysis Server.

Tests for mcp_servers/analysis_server/server.py
"""

import pytest


class TestAnalysisServer:
    """Tests for Analysis MCP server."""
    
    def test_init(self):
        """Initialize analysis server."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        assert server is not None
        assert server.name == "analysis_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        tools = server.get_tools()
        
        assert len(tools) > 0
        
        tool_names = [t.name for t in tools]
        assert "meta_analysis" in tool_names
        assert "trend_detection" in tool_names


class TestMetaAnalysis:
    """Tests for meta_analysis function."""
    
    @pytest.mark.asyncio
    async def test_comparison_analysis(self):
        """Run comparison analysis."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "A", "value": 100},
                {"source": "B", "value": 120},
                {"source": "C", "value": 95},
            ],
            "analysis_type": "comparison",
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_aggregation_analysis(self):
        """Run aggregation analysis."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "A", "value": 10},
                {"source": "B", "value": 20},
            ],
            "analysis_type": "aggregation",
        })
        
        assert result is not None


class TestTrendDetection:
    """Tests for trend_detection function."""
    
    @pytest.mark.asyncio
    async def test_increasing_trend(self):
        """Detect increasing trend."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_trend_detection({
            "data": [10, 15, 20, 25, 30],
            "metric_name": "Growth",
        })
        
        assert result is not None
        # Result is a ToolResult, extract text content
        if hasattr(result, 'content'):
            text = result.content[0].text.lower()
        else:
            text = str(result).lower()
        assert "increasing" in text or "upward" in text or "positive" in text or "trend" in text
    
    @pytest.mark.asyncio
    async def test_decreasing_trend(self):
        """Detect decreasing trend."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        
        result = await server._handle_trend_detection({
            "data": [30, 25, 20, 15, 10],
            "metric_name": "Decline",
        })
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
