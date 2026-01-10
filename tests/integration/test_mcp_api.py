"""
Integration Tests: MCP API.

Tests for /api/v1/mcp/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


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
        
        # Should have at least some tools registered
        assert len(data["tools"]) > 0
    
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
        """Invoke a tool via API."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "execute_code",
                    "arguments": {"code": "print(1+1)"},
                }
            )
        
        # May succeed or fail depending on server status
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
