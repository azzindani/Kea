"""
Tests for MCP transport layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.mcp.transport import (
    Transport,
    StdioTransport,
    SSETransport,
)
from shared.mcp.protocol import JSONRPCRequest, JSONRPCResponse


class TestTransport:
    """Tests for Transport abstract base class."""
    
    def test_transport_is_abstract(self):
        """Test that Transport cannot be instantiated."""
        with pytest.raises(TypeError):
            Transport()


class TestStdioTransport:
    """Tests for StdioTransport."""
    
    @pytest.fixture
    def transport(self):
        return StdioTransport()
    
    def test_stdio_init(self, transport):
        """Test StdioTransport initialization."""
        assert transport._reader is None
        assert transport._writer is None
        assert transport._closed is False
    
    @pytest.mark.asyncio
    async def test_send_without_start(self, transport):
        """Test that send raises error if not started."""
        request = JSONRPCRequest(id="1", method="test")
        
        with pytest.raises(RuntimeError, match="Transport not started"):
            await transport.send(request)
    
    @pytest.mark.asyncio
    async def test_close(self, transport):
        """Test closing transport."""
        await transport.close()
        assert transport._closed is True


class TestSSETransport:
    """Tests for SSETransport."""
    
    @pytest.fixture
    def transport(self):
        return SSETransport(url="http://localhost:8000/sse")
    
    def test_sse_init(self, transport):
        """Test SSETransport initialization."""
        assert transport.url == "http://localhost:8000/sse"
        assert transport._queue is not None
        assert transport._closed is False
    
    @pytest.mark.asyncio
    async def test_close(self, transport):
        """Test closing SSE transport."""
        await transport.close()
        assert transport._closed is True
    
    @pytest.mark.asyncio
    async def test_send_message(self, transport):
        """Test sending message via SSE."""
        request = JSONRPCRequest(id="1", method="test")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post = AsyncMock()
            
            await transport.send(request)
            
            mock_instance.post.assert_called_once()
