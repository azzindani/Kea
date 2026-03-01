"""
SQL Query Tool.

DuckDB SQL queries on in-memory data.
"""

from __future__ import annotations

import io
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger


logger = get_logger(__name__)


async def sql_query_tool(arguments: dict) -> ToolResult:
    """
    Execute SQL query using DuckDB.
    
    Args:
        arguments: Tool arguments containing:
            - query: SQL query to execute
            - data_sources: Map of table names to data
    
    Returns:
        ToolResult with query results
    """
    query = arguments.get("query", "")
    data_sources = arguments.get("data_sources") or {}
    
    if not query:
        return ToolResult(
            content=[TextContent(text="Error: Query is required")],
            isError=True
        )
    
    try:
        import duckdb
        import pandas as pd
    except ImportError:
        return ToolResult(
            content=[TextContent(text="Error: DuckDB or Pandas not installed")],
            isError=True
        )
    
    try:
        # Create in-memory database
        conn = duckdb.connect(":memory:")
        
        # Register data sources as tables
        for table_name, data in data_sources.items():
            if isinstance(data, str):
                if data.startswith("http"):
                    # URL - load directly
                    df = pd.read_csv(data)
                elif data.strip().startswith("{") or data.strip().startswith("["):
                    # JSON
                    import json
                    df = pd.DataFrame(json.loads(data))
                else:
                    # CSV string
                    df = pd.read_csv(io.StringIO(data))
            elif isinstance(data, dict):
                df = pd.DataFrame(data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                continue
            
            conn.register(table_name, df)
        
        # Execute query
        result = conn.execute(query).fetchdf()
        
        # Format output
        output = f"## Query Results\n\n"
        output += f"**Query:**\n```sql\n{query}\n```\n\n"
        output += f"**Rows returned:** {len(result)}\n\n"
        
        if len(result) > 0:
            output += f"**Results:**\n```\n{result.head(100).to_string()}\n```"
            
            if len(result) > 100:
                output += f"\n\n*Showing first 100 of {len(result)} rows*"
        else:
            output += "*No rows returned*"
        
        conn.close()
        
        return ToolResult(content=[TextContent(text=output)])
        
    except Exception as e:
        logger.error(f"SQL query error: {e}")
        return ToolResult(
            content=[TextContent(text=f"SQL Error: {str(e)}")],
            isError=True
        )
