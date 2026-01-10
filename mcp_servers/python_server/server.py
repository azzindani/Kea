"""
Python MCP Server.

Provides sandboxed Python execution tools via MCP protocol.
"""

from __future__ import annotations

import asyncio

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

from mcp_servers.python_server.tools.execute_code import execute_code_tool
from mcp_servers.python_server.tools.dataframe_ops import dataframe_ops_tool
from mcp_servers.python_server.tools.sql_query import sql_query_tool


logger = get_logger(__name__)


class PythonServer(MCPServer):
    """
    MCP Server for Python execution.
    
    Tools:
    - execute_code: Run Python code
    - dataframe_ops: Pandas operations
    - sql_query: DuckDB SQL queries
    """
    
    def __init__(self) -> None:
        super().__init__(name="python_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all Python tools."""
        
        # execute_code tool
        self.register_tool(
            name="execute_code",
            description="Execute Python code in a sandboxed environment. Returns stdout, variables, and any errors.",
            handler=self._handle_execute_code,
            parameters={
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds (default: 30)"
                }
            },
            required=["code"]
        )
        
        # dataframe_ops tool
        self.register_tool(
            name="dataframe_ops",
            description="Perform Pandas DataFrame operations. Load, transform, and analyze data.",
            handler=self._handle_dataframe_ops,
            parameters={
                "operation": {
                    "type": "string",
                    "description": "Operation: load_csv, load_json, describe, filter, aggregate, join"
                },
                "data": {
                    "type": "string",
                    "description": "CSV/JSON data or URL"
                },
                "params": {
                    "type": "object",
                    "description": "Operation-specific parameters"
                }
            },
            required=["operation"]
        )
        
        # sql_query tool
        self.register_tool(
            name="sql_query",
            description="Execute SQL query on in-memory data using DuckDB. Supports CSV/Parquet/JSON data sources.",
            handler=self._handle_sql_query,
            parameters={
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "data_sources": {
                    "type": "object",
                    "description": "Map of table names to data (CSV string, URL, or JSON)"
                }
            },
            required=["query"]
        )
    
    async def _handle_execute_code(self, arguments: dict) -> ToolResult:
        """Handle execute_code tool call."""
        logger.info("Executing Python code")
        return await execute_code_tool(arguments)
    
    async def _handle_dataframe_ops(self, arguments: dict) -> ToolResult:
        """Handle dataframe_ops tool call."""
        logger.info("Executing DataFrame operation", extra={"op": arguments.get("operation")})
        return await dataframe_ops_tool(arguments)
    
    async def _handle_sql_query(self, arguments: dict) -> ToolResult:
        """Handle sql_query tool call."""
        logger.info("Executing SQL query")
        return await sql_query_tool(arguments)


async def main() -> None:
    """Run the Python server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="python_server"))
    
    server = PythonServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
