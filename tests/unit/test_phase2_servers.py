"""
Unit Tests: Phase 2 MCP Servers.

Tests for academic_server, regulatory_server, browser_agent_server.
"""

import pytest


class TestAcademicServer:
    """Tests for academic server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.academic_server import AcademicServer
        
        server = AcademicServer()
        assert server.name == "academic_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.academic_server import AcademicServer
        
        server = AcademicServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "pubmed_search" in tool_names
        assert "arxiv_search" in tool_names
        assert "semantic_scholar_search" in tool_names
        assert "crossref_lookup" in tool_names


class TestRegulatoryServer:
    """Tests for regulatory server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.regulatory_server import RegulatoryServer
        
        server = RegulatoryServer()
        assert server.name == "regulatory_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.regulatory_server import RegulatoryServer
        
        server = RegulatoryServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "edgar_search" in tool_names
        assert "ecfr_search" in tool_names
        assert "federal_register_search" in tool_names


class TestBrowserAgentServer:
    """Tests for browser agent server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.browser_agent_server import BrowserAgentServer
        
        server = BrowserAgentServer()
        assert server.name == "browser_agent_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.browser_agent_server import BrowserAgentServer
        
        server = BrowserAgentServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "human_like_search" in tool_names
        assert "source_validator" in tool_names
        assert "search_memory_add" in tool_names


class TestToolIntegrationPhase2:
    """Integration tests for Phase 2 tools."""
    
    @pytest.mark.asyncio
    async def test_arxiv_search(self):
        """Search arXiv."""
        from mcp_servers.academic_server import arxiv_search_tool
        
        result = await arxiv_search_tool({
            "query": "machine learning",
            "max_results": 3,
        })
        
        assert not result.isError
        assert "arXiv" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_source_validator(self):
        """Validate source credibility."""
        from mcp_servers.browser_agent_server import source_validator_tool
        
        result = await source_validator_tool({
            "url": "https://www.nature.com/articles/example",
        })
        
        assert not result.isError
        assert "Credibility" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
