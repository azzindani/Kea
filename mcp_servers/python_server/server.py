
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.python_server.tools import execute_code as execute_code_module, dataframe_ops as dataframe_ops_module, sql_query as sql_query_module
import structlog
import asyncio
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

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
    """EXECUTES python code. [ACTION]
    
    [RAG Context]
    Execute Python code in a sandboxed environment.
    Returns stdout, variables, and any errors.
    """
    return await run_op(execute_code_module.execute_code_tool, code=code, timeout=timeout, dependencies=dependencies)

@mcp.tool()
async def dataframe_ops(
    operation: str,
    data: str = None,
    params: Dict[str, Any] = None
) -> str:
    """MANIPULATES DataFrame. [ACTION]
    
    [RAG Context]
    Perform Pandas DataFrame operations (load, filter, aggregate).
    Returns result string.
    """
    return await run_op(dataframe_ops_module.dataframe_ops_tool, operation=operation, data=data, params=params)

@mcp.tool()
async def sql_query(
    query: str,
    data_sources: Dict[str, Any] = None
) -> str:
    """EXECUTES SQL. [ACTION]
    
    [RAG Context]
    Execute SQL query on in-memory data using DuckDB.
    Returns result table.
    """
    return await run_op(sql_query_module.sql_query_tool, query=query, data_sources=data_sources)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PythonServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

