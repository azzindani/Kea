
from mcp.server.fastmcp import FastMCP
from mcp_servers.python_server.tools import execute_code, dataframe_ops, sql_query
import structlog
import asyncio
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("python_server")

async def run_op(op_func, diff_args=None, **kwargs):
    """Helper to run legacy tool ops."""
    try:
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        result = await op_func(final_args) # Note: These tools expect a single 'arguments' dict
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
            
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

@mcp.tool()
async def execute_code(
    code: str,
    timeout: int = 30,
    dependencies: List[str] = []
) -> str:
    """
    Execute Python code in a sandboxed environment.
    Returns stdout, variables, and any errors.
    """
    return await run_op(execute_code.execute_code_tool, code=code, timeout=timeout, dependencies=dependencies)

@mcp.tool()
async def dataframe_ops(
    operation: str,
    data: str = None,
    params: Dict[str, Any] = None
) -> str:
    """
    Perform Pandas DataFrame operations.
    operation: load_csv, load_json, describe, filter, aggregate, join
    """
    return await run_op(dataframe_ops.dataframe_ops_tool, operation=operation, data=data, params=params)

@mcp.tool()
async def sql_query(
    query: str,
    data_sources: Dict[str, Any] = None
) -> str:
    """
    Execute SQL query on in-memory data using DuckDB.
    Supports CSV/Parquet/JSON data sources.
    """
    return await run_op(sql_query.sql_query_tool, query=query, data_sources=data_sources)

if __name__ == "__main__":
    mcp.run()
