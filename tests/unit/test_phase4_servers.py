"""
Unit Tests: Phase 4 MCP Servers - Tool Discovery.

Tests for tool_discovery_server.
"""

import pytest


class TestToolDiscoveryServer:
    """Tests for tool discovery server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.tool_discovery_server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        assert server.name == "tool_discovery_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.tool_discovery_server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "search_pypi" in tool_names
        assert "search_npm" in tool_names
        assert "package_info" in tool_names
        assert "evaluate_package" in tool_names
        assert "generate_mcp_stub" in tool_names
        assert "suggest_tools" in tool_names


class TestToolDiscoveryFunctions:
    """Tests for tool discovery functions."""
    
    @pytest.mark.asyncio
    async def test_search_pypi(self):
        """Search PyPI for packages."""
        from mcp_servers.tool_discovery_server import search_pypi_tool
        
        result = await search_pypi_tool({
            "query": "data analysis",
            "max_results": 5,
        })
        
        assert not result.isError
        assert "PyPI" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_evaluate_package(self):
        """Evaluate package for MCP integration."""
        from mcp_servers.tool_discovery_server import evaluate_package_tool
        
        result = await evaluate_package_tool({
            "package_name": "pandas",
            "use_case": "data analysis",
        })
        
        assert not result.isError
        assert "Evaluation" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_generate_stub(self):
        """Generate MCP stub code."""
        from mcp_servers.tool_discovery_server import generate_mcp_stub_tool
        
        result = await generate_mcp_stub_tool({
            "package_name": "my-package",
            "functions": ["analyze", "transform"],
            "server_name": "my_server",
        })
        
        assert not result.isError
        assert "class" in result.content[0].text
        assert "def get_tools" in result.content[0].text


class TestToolRegistry:
    """Tests for tool registry functions."""
    
    @pytest.mark.asyncio
    async def test_registry_add_and_list(self):
        """Test adding and listing registry entries."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        
        # Add to registry
        add_result = await server._handle_registry_add({
            "package_name": "test-package",
            "tool_type": "analysis",
            "priority": "high",
        })
        
        assert not add_result.isError
        assert "Added" in add_result.content[0].text
        
        # List registry
        list_result = await server._handle_registry_list({})
        
        assert not list_result.isError
        assert "test-package" in list_result.content[0].text


class TestSuggestions:
    """Tests for tool suggestions."""
    
    @pytest.mark.asyncio
    async def test_suggest_finance_tools(self):
        """Suggest tools for finance domain."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        result = await server._handle_suggest({
            "research_domain": "finance",
            "task_type": "data",
        })
        
        assert not result.isError
        assert "yfinance" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
