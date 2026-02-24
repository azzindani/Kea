"""
Unit Tests: Tool Registry.

Tests for services/orchestrator/mcp/registry.py.
"""

import pytest


class TestToolRegistry:
    """Tests for MCP tool registry."""

    def test_register_builtin_tools(self):
        """Register built-in tools."""
        from services.orchestrator.mcp.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_builtin_tools()

        tools = registry.list_tools()

        assert len(tools) > 0
        assert any(t.name == "fetch_url" for t in tools)
        assert any(t.name == "web_search" for t in tools)

    def test_get_tool(self):
        """Get tool by name."""
        from services.orchestrator.mcp.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_builtin_tools()

        tool = registry.get_tool("fetch_url")

        assert tool is not None
        assert tool.name == "fetch_url"
        assert tool.server_name == "scraper_server"

    def test_get_server_for_tool(self):
        """Get server name for tool."""
        from services.orchestrator.mcp.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_builtin_tools()

        server = registry.get_server_for_tool("execute_code")

        assert server == "python_server"

    def test_list_tools_by_server(self):
        """List tools filtered by server."""
        from services.orchestrator.mcp.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_builtin_tools()

        scraper_tools = registry.list_tools(server_name="scraper_server")

        assert len(scraper_tools) >= 2
        assert all(t.server_name == "scraper_server" for t in scraper_tools)

    def test_update_tool_stats(self):
        """Update tool usage statistics."""
        from services.orchestrator.mcp.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_builtin_tools()

        registry.update_tool_stats("fetch_url", 100.0)
        registry.update_tool_stats("fetch_url", 200.0)

        tool = registry.get_tool("fetch_url")

        assert tool.call_count == 2
        assert tool.avg_duration_ms == 150.0


class TestGlobalRegistry:
    """Tests for global registry singleton."""

    def test_get_registry(self):
        """Get global registry."""
        from services.orchestrator.mcp.registry import get_registry

        registry = get_registry()

        assert registry is not None
        assert len(registry.list_tools()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
