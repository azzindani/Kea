"""
Unit Tests: MCP Protocol.

Tests for shared/mcp/protocol.py JSON-RPC implementation.
"""

import pytest


class TestJSONRPCRequest:
    """Tests for JSON-RPC request parsing."""

    def test_create_request(self):
        """Create valid JSON-RPC request."""
        from shared.mcp.protocol import JSONRPCRequest

        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/list",
            id=1,
        )

        assert req.jsonrpc == "2.0"
        assert req.method == "tools/list"
        assert req.id == 1

    def test_request_with_params(self):
        """Request with parameters."""
        from shared.mcp.protocol import JSONRPCRequest

        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=2,
            params={"name": "fetch_url", "arguments": {"url": "test"}},
        )

        assert req.params["name"] == "fetch_url"

    def test_notification_no_id(self):
        """Notification has no id - use JSONRPCNotification class."""
        from shared.mcp.protocol import JSONRPCNotification

        notif = JSONRPCNotification(
            jsonrpc="2.0",
            method="notifications/message",
        )

        # JSONRPCNotification doesn't have id field
        assert notif.method == "notifications/message"
        assert not hasattr(notif, 'id') or getattr(notif, 'id', None) is None


class TestJSONRPCResponse:
    """Tests for JSON-RPC response creation."""

    def test_success_response(self):
        """Create success response."""
        from shared.mcp.protocol import JSONRPCResponse

        resp = JSONRPCResponse(
            jsonrpc="2.0",
            id=1,
            result={"tools": []},
        )

        assert resp.result == {"tools": []}
        assert resp.error is None

    def test_error_response(self):
        """Create error response."""
        from shared.mcp.protocol import JSONRPCError, JSONRPCResponse

        resp = JSONRPCResponse(
            jsonrpc="2.0",
            id=1,
            error=JSONRPCError(code=-32600, message="Invalid Request"),
        )

        assert resp.error is not None
        assert resp.error.code == -32600


class TestTool:
    """Tests for Tool definition."""

    def test_create_tool(self):
        """Create tool definition."""
        from shared.mcp.protocol import Tool, ToolInputSchema

        tool = Tool(
            name="fetch_url",
            description="Fetch URL content",
            inputSchema=ToolInputSchema(
                type="object",
                properties={"url": {"type": "string"}},
                required=["url"],
            ),
        )

        assert tool.name == "fetch_url"
        assert "url" in tool.inputSchema.properties


class TestToolResult:
    """Tests for ToolResult."""

    def test_success_result(self):
        """Create success result."""
        from shared.mcp.protocol import TextContent, ToolResult

        result = ToolResult(
            content=[TextContent(text="Success!")],
            isError=False,
        )

        assert not result.isError
        assert result.content[0].text == "Success!"

    def test_error_result(self):
        """Create error result."""
        from shared.mcp.protocol import TextContent, ToolResult

        result = ToolResult(
            content=[TextContent(text="Error occurred")],
            isError=True,
        )

        assert result.isError


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
