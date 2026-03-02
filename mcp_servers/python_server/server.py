
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
from shared.logging.decorators import trace_io
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
@trace_io()
async def execute_code(
    code: str,
    timeout: int = 30,
    dependencies: List[str] = []
) -> str:
    """EXECUTES python code. [ACTION]
    
    [RAG Context]
    Runs arbitrary Python 3.12+ code in a secure, isolated sandboxed environment. This is the primary tool for custom logic, data transformation, and complex algorithmic processing that isn't covered by other specialized tools.
    
    How to Use:
    - Provide raw Python code as a string.
    - If you need external libraries (e.g., 'scikit-learn', 'requests'), list them in the 'dependencies' argument. The system will install them JIT.
    - Captures all standard output (print statements) and returns it alongside the final state of local variables.
    - Handles timeouts (default 30s) to prevent runaway processes.
    
    Arguments:
    - code (str): The Python script to run.
    - timeout (int): Maximum execution time in seconds.
    - dependencies (List[str]): List of PyPI packages to install before running.
    
    Example:
    - Input: code="import math; print(math.sqrt(144))"
    - Output: "12.0"
    
    Keywords: run script, python sandbox, custom logic, code execution, jit dependencies.
    """
    return await run_op(execute_code_module.execute_code_tool, code=code, timeout=timeout, dependencies=dependencies)

@mcp.tool()
@trace_io()
async def dataframe_ops(
    operation: str,
    data: str = None,
    params: Dict[str, Any] = None
) -> str:
    """MANIPULATES DataFrame. [ACTION]
    
    [RAG Context]
    High-level interface for Pandas-style data manipulation. Designed for non-programmatic data scientists to perform common table operations.
    
    Operations Supported:
    - 'load': Read CSV/JSON data into a DataFrame.
    - 'filter': Select rows based on conditions.
    - 'aggregate': Compute group-by statistics (mean, sum, count).
    - 'sort': Order data by one or more columns.
    - 'merge': Join two datasets.
    
    How to Use:
    - Pass the operation name and the data source (either raw string or a reference to a previous output).
    - Use 'params' to specify columns, conditions, and sorting orders.
    
    Arguments:
    - operation (str): One of the supported verbs.
    - data (str): The raw input data string.
    - params (Dict): Configuration for the operation.
    
    Keywords: pandas, data processing, filtering, aggregation, table manipulation.
    """
    return await run_op(dataframe_ops_module.dataframe_ops_tool, operation=operation, data=data, params=params)

@mcp.tool()
@trace_io()
async def sql_query(
    query: str,
    data_sources: Dict[str, Any] = None
) -> str:
    """EXECUTES SQL. [ACTION]
    
    [RAG Context]
    Executes standard SQL queries against in-memory datasets using the DuckDB engine. This is ideal for querying large CSV/JSON extracts without loading them into a full database.
    
    How to Use:
    - Write standard SQL (SELECT, JOIN, GROUP BY).
    - Provide 'data_sources' as a mapping of table names to raw data strings. DuckDB will automatically parse them.
    - Returns a formatted table result.
    
    Arguments:
    - query (str): The SQL query string.
    - data_sources (Dict): e.g., {"users": "id,name\n1,Alice"}
    
    Example:
    - Input: query="SELECT * FROM data WHERE price > 100"
    
    Keywords: duckdb, in-memory sql, relational query, table search, data analysis.
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

