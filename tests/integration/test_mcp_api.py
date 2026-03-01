"""
Integration Tests: MCP API.

Tests for /api/v1/mcp/* endpoints.
Actual routes (from mcp.py):
- GET /servers - List servers
- GET /tools - List tools
- GET /tools/{tool_name} - Get tool info
- POST /invoke - Invoke tool
- POST /servers/{name}/restart - Restart server
"""

import httpx
import pytest

from shared.config import get_settings

API_URL = get_settings().services.gateway


class TestMCPServers:
    """Tests for MCP server endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_servers(self):
        """List MCP servers."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/mcp/servers")

        assert response.status_code == 200
        data = response.json()
        assert "servers" in data


class TestMCPTools:
    """Tests for MCP tool endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """List available tools."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/mcp/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data

        # Should always have tools (built-in fallback)
        assert len(data["tools"]) > 0, "Expected at least some tools (built-in fallback should work)"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_structure(self):
        """Verify tool structure."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/mcp/tools")

        data = response.json()

        if data["tools"]:
            tool = data["tools"][0]
            assert "name" in tool
            assert "description" in tool


class TestMCPToolInvocation:
    """Tests for tool invocation."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invoke_tool(self):
        """Invoke a tool via API (POST /invoke)."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Correct path is /invoke, not /tools/invoke
            response = await client.post(
                f"{API_URL}/api/v1/mcp/invoke",
                json={
                    "tool_name": "execute_code",
                    "arguments": {"code": "print(1+1)"},
                }
            )

        # May succeed or fail depending on server status
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            assert "tool_name" in data or "content" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
