"""
Unit Tests: Phase 3 MCP Servers.

Tests for qualitative_server and security_server.
"""

import pytest


class TestQualitativeServer:
    """Tests for qualitative server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.qualitative_server import QualitativeServer
        
        server = QualitativeServer()
        assert server.name == "qualitative_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.qualitative_server import QualitativeServer
        
        server = QualitativeServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "text_coding" in tool_names
        assert "theme_extractor" in tool_names
        assert "entity_extractor" in tool_names
        assert "investigation_graph_add" in tool_names
        assert "snowball_sampling" in tool_names
        assert "triangulation_check" in tool_names


class TestSecurityServer:
    """Tests for security server."""
    
    def test_init(self):
        """Initialize server."""
        from mcp_servers.security_server import SecurityServer
        
        server = SecurityServer()
        assert server.name == "security_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.security_server import SecurityServer
        
        server = SecurityServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        assert "url_scanner" in tool_names
        assert "content_sanitizer" in tool_names
        assert "file_hash_check" in tool_names
        assert "code_safety_check" in tool_names


class TestQualitativeTools:
    """Tests for qualitative analysis tools."""
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self):
        """Extract entities from text."""
        from mcp_servers.qualitative_server import entity_extractor_tool
        
        result = await entity_extractor_tool({
            "text": "John Smith met with Microsoft CEO in New York on January 15, 2024 to discuss $1 million deal.",
        })
        
        assert not result.isError
        assert "Entity" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_triangulation(self):
        """Test triangulation check."""
        from mcp_servers.qualitative_server import triangulation_tool
        
        result = await triangulation_tool({
            "claim": "Indonesia is top nickel producer",
            "sources": [
                {"text": "Indonesia produced 1.6M tons", "credibility": 0.9, "supports": True},
                {"text": "Indonesia leads nickel output", "credibility": 0.85, "supports": True},
            ],
            "min_sources": 2,
        })
        
        assert not result.isError
        assert "VERIFIED" in result.content[0].text


class TestSecurityTools:
    """Tests for security tools."""
    
    @pytest.mark.asyncio
    async def test_url_scanner(self):
        """Scan URL for threats."""
        from mcp_servers.security_server import url_scanner_tool
        
        result = await url_scanner_tool({
            "url": "https://www.nature.com/articles/example",
        })
        
        assert not result.isError
        assert "SAFE" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_content_sanitizer(self):
        """Test content sanitization."""
        from mcp_servers.security_server import content_sanitizer_tool
        
        result = await content_sanitizer_tool({
            "content": "<script>alert('xss')</script>Hello World",
        })
        
        assert not result.isError
        assert "Hello World" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_code_safety(self):
        """Test code safety check."""
        from mcp_servers.security_server import code_safety_tool
        
        result = await code_safety_tool({
            "code": "exec(user_input)",
            "language": "python",
        })
        
        assert not result.isError
        assert "UNSAFE" in result.content[0].text or "exec" in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
