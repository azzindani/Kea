"""
Unit Tests: New MCP Servers.

Tests for data_sources, analytics, crawler, ml, visualization, document servers.
"""

import pytest


class TestDataSourcesServer:
    """Tests for data sources server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.data_sources_server import DataSourcesServer
        
        server = DataSourcesServer()
        assert server.name == "data_sources_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.data_sources_server import DataSourcesServer
        
        server = DataSourcesServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "yfinance_fetch" in tool_names
        assert "csv_fetch" in tool_names


class TestAnalyticsServerNew:
    """Tests for analytics server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.analytics_server import AnalyticsServer
        
        server = AnalyticsServer()
        assert server.name == "analytics_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.analytics_server import AnalyticsServer
        
        server = AnalyticsServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "eda_auto" in tool_names
        assert "data_cleaner" in tool_names


class TestCrawlerServer:
    """Tests for crawler server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.crawler_server import CrawlerServer
        
        server = CrawlerServer()
        assert server.name == "crawler_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.crawler_server import CrawlerServer
        
        server = CrawlerServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "web_crawler" in tool_names
        assert "sitemap_parser" in tool_names


class TestMLServer:
    """Tests for ML server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.ml_server import MLServer
        
        server = MLServer()
        assert server.name == "ml_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.ml_server import MLServer
        
        server = MLServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "auto_ml" in tool_names
        assert "clustering" in tool_names


class TestVisualizationServer:
    """Tests for visualization server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.visualization_server import VisualizationServer
        
        server = VisualizationServer()
        assert server.name == "visualization_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.visualization_server import VisualizationServer
        
        server = VisualizationServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "plotly_chart" in tool_names


class TestDocumentServer:
    """Tests for document server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.document_server import DocumentServer
        
        server = DocumentServer()
        assert server.name == "document_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.document_server import DocumentServer
        
        server = DocumentServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "pdf_parser" in tool_names
        assert "xlsx_parser" in tool_names


class TestToolIntegration:
    """Integration tests for tool functions."""
    
    @pytest.mark.asyncio
    async def test_csv_fetch(self):
        """Fetch CSV from sample URL."""
        from mcp_servers.data_sources_server import csv_fetch_tool
        
        result = await csv_fetch_tool({
            "url": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
            "preview_rows": 3,
        })
        
        assert not result.isError
        assert "Adidas" in result.content[0].text or "rows" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_eda_auto(self):
        """Run EDA on sample data."""
        from mcp_servers.analytics_server import eda_auto_tool
        
        result = await eda_auto_tool({
            "data_url": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
        })
        
        assert not result.isError
        assert "Dataset Overview" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
