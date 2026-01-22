"""
MCP Logging Middleware.

Middleware for logging MCP JSON-RPC requests and responses.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from shared.mcp.protocol import JSONRPCRequest, JSONRPCResponse, ToolResult
from shared.logging import get_logger
from shared.logging.context import set_log_context, get_log_context
from shared.logging.metrics import record_tool_call
import os


logger = get_logger(__name__)


class MCPLoggingMiddleware:
    """
    Middleware for logging MCP requests and responses.
    
    Features:
    - Log all tool invocations
    - Track timing
    - Record metrics
    - Correlate with trace IDs
    
    Example:
        middleware = MCPLoggingMiddleware()
        
        @middleware.wrap
        async def handle_request(request: JSONRPCRequest):
            # Handle request
            pass
    """
    
    def __init__(self, server_name: str = "unknown") -> None:
        self.server_name = server_name
    
    def wrap(
        self,
        handler: Callable[[JSONRPCRequest], Awaitable[JSONRPCResponse]],
    ) -> Callable[[JSONRPCRequest], Awaitable[JSONRPCResponse]]:
        """Wrap a request handler with logging."""
        
        async def wrapped(request: JSONRPCRequest) -> JSONRPCResponse:
            start_time = time.perf_counter()
            
            # Log request
            method = request.method
            request_id = str(request.id) if request.id else "notification"
            
            if os.getenv("KEA_LOG_NO_TRUNCATE") == "1" and request.params:
                # Log full parameters in verbose mode
                # Note: We duplicate params here for visibility, normally only method/id are logged
                logger.info(
                   f"MCP params: {method}",
                   extra={"arguments": request.params, "mcp_request_id": request_id}
                )

            logger.info(
                f"MCP request: {method}",
                extra={
                    "mcp_method": method,
                    "mcp_request_id": request_id,
                    "mcp_server": self.server_name,
                }
            )
            
            try:
                # Execute handler
                response = await handler(request)
                
                duration = time.perf_counter() - start_time
                
                # Log response
                is_error = response.error is not None
                
                if is_error:
                    logger.warning(
                        f"MCP error: {method} - {response.error.message}",
                        extra={
                            "mcp_method": method,
                            "mcp_request_id": request_id,
                            "mcp_error_code": response.error.code,
                            "duration_ms": duration * 1000,
                        }
                    )
                else:
                    logger.info(
                        f"MCP response: {method}",
                        extra={
                            "mcp_method": method,
                            "mcp_request_id": request_id,
                            "duration_ms": duration * 1000,
                        }
                    )
                
                # Record metrics for tool calls
                if method == "tools/call" and request.params:
                    tool_name = request.params.get("name", "unknown")
                    record_tool_call(
                        tool_name=tool_name,
                        server_name=self.server_name,
                        duration=duration,
                        success=not is_error,
                    )
                
                return response
                
            except Exception as e:
                duration = time.perf_counter() - start_time
                
                logger.error(
                    f"MCP exception: {method} - {str(e)}",
                    extra={
                        "mcp_method": method,
                        "mcp_request_id": request_id,
                        "duration_ms": duration * 1000,
                    },
                    exc_info=True,
                )
                raise
        
        return wrapped
    
    async def log_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        result: ToolResult,
        duration_ms: float,
    ) -> None:
        """Log a tool call with its result."""
        is_error = result.isError
        
        log_level = "warning" if is_error else "info"
        
        log_data = {
            "tool_name": tool_name,
            "server_name": self.server_name,
            "duration_ms": duration_ms,
            "is_error": is_error,
            "argument_keys": list(arguments.keys()),
        }
        
        if is_error and result.content:
            log_data["error_preview"] = result.content[0].text[:200]
        
        no_truncate = os.getenv("KEA_LOG_NO_TRUNCATE") == "1"
        if no_truncate:
             log_data["arguments"] = arguments
             # Flatten content list into readable string
             if result.content:
                 log_data["result"] = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
             else:
                 log_data["result"] = "Empty content"
        
        getattr(logger, log_level)(
            f"Tool call: {tool_name}",
            extra=log_data,
        )
        
        record_tool_call(
            tool_name=tool_name,
            server_name=self.server_name,
            duration=duration_ms / 1000,
            success=not is_error,
        )


def create_mcp_middleware(server_name: str) -> MCPLoggingMiddleware:
    """Create MCP logging middleware for a server."""
    return MCPLoggingMiddleware(server_name=server_name)
