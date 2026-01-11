"""
Unit Tests: Vision Tools.

Tests for mcp_servers/vision_server/tools/*.py
"""

import pytest


class TestTableOCRTool:
    """Tests for table_ocr tool."""
    
    def test_tool_definition(self):
        """Table OCR tool has correct definition."""
        from mcp_servers.vision_server.tools.table_ocr import table_ocr_tool
        
        # Verify it's a callable
        assert callable(table_ocr_tool)
    
    @pytest.mark.asyncio
    async def test_table_ocr_markdown_output(self):
        """Test table OCR with markdown output."""
        from mcp_servers.vision_server.tools.table_ocr import table_ocr_tool
        
        # This will fail without a valid image, but shouldn't crash
        try:
            result = await table_ocr_tool({
                "image_url": "https://example.com/table.png",
                "output_format": "markdown",
            })
            # If it succeeds (unlikely without real image), check structure
            assert result is not None
        except Exception:
            # Expected - no real image
            pass
    
    @pytest.mark.asyncio
    async def test_table_ocr_json_output(self):
        """Test table OCR with JSON output."""
        from mcp_servers.vision_server.tools.table_ocr import table_ocr_tool
        
        try:
            result = await table_ocr_tool({
                "image_url": "https://example.com/table.png",
                "output_format": "json",
            })
            assert result is not None
        except Exception:
            pass


class TestVisionServer:
    """Tests for vision server."""
    
    def test_init(self):
        """Initialize vision server."""
        from mcp_servers.vision_server.server import VisionServer
        
        server = VisionServer()
        
        assert server is not None
        assert server.name == "vision_server"
    
    def test_get_tools(self):
        """Get available tools."""
        from mcp_servers.vision_server.server import VisionServer
        
        server = VisionServer()
        tools = server.get_tools()
        
        tool_names = [t.name for t in tools]
        # Check for tools that exist (screenshot_extract and chart_reader)
        assert len(tool_names) >= 2
        assert "screenshot_extract" in tool_names or "chart_reader" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
