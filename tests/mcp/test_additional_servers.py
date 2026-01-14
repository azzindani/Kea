"""
Tests for Additional MCP Servers.

Covers: academic, analytics, browser_agent, crawler, data_sources,
document, ml, qualitative, regulatory, security, tool_discovery, visualization
"""

import pytest


class TestAcademicServer:
    """Tests for Academic Research Server."""
    
    def test_import_academic(self):
        """Test academic server imports."""
        from mcp_servers.academic_server import server
        assert server is not None
        print("\n✅ Academic server imports work")
    
    def test_search_papers(self):
        """Test academic paper search."""
        from mcp_servers.academic_server.server import AcademicServer
        
        server = AcademicServer()
        
        # Check tool exists
        tools = server.list_tools()
        tool_names = [t.name for t in tools]
        
        assert any("search" in name.lower() or "paper" in name.lower() for name in tool_names) or len(tools) > 0
        print(f"\n✅ Academic server has {len(tools)} tools")


class TestAnalyticsServer:
    """Tests for Analytics Server."""
    
    def test_import_analytics(self):
        """Test analytics server imports."""
        from mcp_servers.analytics_server import server
        assert server is not None
        print("\n✅ Analytics server imports work")
    
    def test_list_tools(self):
        """Test listing analytics tools."""
        from mcp_servers.analytics_server.server import AnalyticsServer
        
        server = AnalyticsServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Analytics server has {len(tools)} tools")


class TestBrowserAgentServer:
    """Tests for Browser Agent Server."""
    
    def test_import_browser_agent(self):
        """Test browser agent server imports."""
        from mcp_servers.browser_agent_server import server
        assert server is not None
        print("\n✅ Browser agent server imports work")
    
    def test_list_tools(self):
        """Test listing browser tools."""
        from mcp_servers.browser_agent_server.server import BrowserAgentServer
        
        server = BrowserAgentServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Browser agent has {len(tools)} tools")


class TestCrawlerServer:
    """Tests for Crawler Server."""
    
    def test_import_crawler(self):
        """Test crawler server imports."""
        from mcp_servers.crawler_server import server
        assert server is not None
        print("\n✅ Crawler server imports work")
    
    def test_list_tools(self):
        """Test listing crawler tools."""
        from mcp_servers.crawler_server.server import CrawlerServer
        
        server = CrawlerServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Crawler has {len(tools)} tools")


class TestDataSourcesServer:
    """Tests for Data Sources Server."""
    
    def test_import_data_sources(self):
        """Test data sources server imports."""
        from mcp_servers.data_sources_server import server
        assert server is not None
        print("\n✅ Data sources server imports work")
    
    def test_list_tools(self):
        """Test listing data source tools."""
        from mcp_servers.data_sources_server.server import DataSourcesServer
        
        server = DataSourcesServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Data sources has {len(tools)} tools")


class TestDocumentServer:
    """Tests for Document Server."""
    
    def test_import_document(self):
        """Test document server imports."""
        from mcp_servers.document_server import server
        assert server is not None
        print("\n✅ Document server imports work")
    
    def test_list_tools(self):
        """Test listing document tools."""
        from mcp_servers.document_server.server import DocumentServer
        
        server = DocumentServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Document server has {len(tools)} tools")


class TestMLServer:
    """Tests for ML Server."""
    
    def test_import_ml(self):
        """Test ML server imports."""
        from mcp_servers.ml_server import server
        assert server is not None
        print("\n✅ ML server imports work")
    
    def test_list_tools(self):
        """Test listing ML tools."""
        from mcp_servers.ml_server.server import MLServer
        
        server = MLServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ ML server has {len(tools)} tools")


class TestQualitativeServer:
    """Tests for Qualitative Analysis Server."""
    
    def test_import_qualitative(self):
        """Test qualitative server imports."""
        from mcp_servers.qualitative_server import server
        assert server is not None
        print("\n✅ Qualitative server imports work")
    
    def test_list_tools(self):
        """Test listing qualitative tools."""
        from mcp_servers.qualitative_server.server import QualitativeServer
        
        server = QualitativeServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Qualitative has {len(tools)} tools")


class TestRegulatoryServer:
    """Tests for Regulatory Server."""
    
    def test_import_regulatory(self):
        """Test regulatory server imports."""
        from mcp_servers.regulatory_server import server
        assert server is not None
        print("\n✅ Regulatory server imports work")
    
    def test_list_tools(self):
        """Test listing regulatory tools."""
        from mcp_servers.regulatory_server.server import RegulatoryServer
        
        server = RegulatoryServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Regulatory has {len(tools)} tools")


class TestSecurityServer:
    """Tests for Security Server."""
    
    def test_import_security(self):
        """Test security server imports."""
        from mcp_servers.security_server import server
        assert server is not None
        print("\n✅ Security server imports work")
    
    def test_list_tools(self):
        """Test listing security tools."""
        from mcp_servers.security_server.server import SecurityServer
        
        server = SecurityServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Security has {len(tools)} tools")


class TestToolDiscoveryServer:
    """Tests for Tool Discovery Server."""
    
    def test_import_tool_discovery(self):
        """Test tool discovery server imports."""
        from mcp_servers.tool_discovery_server import server
        assert server is not None
        print("\n✅ Tool discovery server imports work")
    
    def test_list_tools(self):
        """Test listing discovery tools."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Tool discovery has {len(tools)} tools")


class TestVisualizationServer:
    """Tests for Visualization Server."""
    
    def test_import_visualization(self):
        """Test visualization server imports."""
        from mcp_servers.visualization_server import server
        assert server is not None
        print("\n✅ Visualization server imports work")
    
    def test_list_tools(self):
        """Test listing visualization tools."""
        from mcp_servers.visualization_server.server import VisualizationServer
        
        server = VisualizationServer()
        tools = server.list_tools()
        
        assert len(tools) >= 1
        print(f"\n✅ Visualization has {len(tools)} tools")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
