"""
DataFrame Operations Tool.

Pandas DataFrame operations for data analysis.
"""

from __future__ import annotations

import io
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger


logger = get_logger(__name__)


async def dataframe_ops_tool(arguments: dict) -> ToolResult:
    """
    Perform Pandas DataFrame operations.
    
    Args:
        arguments: Tool arguments containing:
            - operation: Operation type
            - data: Data source (CSV/JSON string or URL)
            - params: Operation-specific parameters
    
    Returns:
        ToolResult with operation result
    """
    operation = arguments.get("operation", "")
    data = arguments.get("data", "")
    params = arguments.get("params", {})
    
    if not operation:
        return ToolResult(
            content=[TextContent(text="Error: Operation is required")],
            isError=True
        )
    
    try:
        import pandas as pd
    except ImportError:
        return ToolResult(
            content=[TextContent(text="Error: Pandas not installed")],
            isError=True
        )
    
    try:
        if operation == "load_csv":
            return await _load_csv(data, params)
        elif operation == "load_json":
            return await _load_json(data, params)
        elif operation == "describe":
            return await _describe(data, params)
        elif operation == "filter":
            return await _filter(data, params)
        elif operation == "aggregate":
            return await _aggregate(data, params)
        else:
            return ToolResult(
                content=[TextContent(text=f"Error: Unknown operation: {operation}")],
                isError=True
            )
    except Exception as e:
        logger.error(f"DataFrame operation error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Error: {str(e)}")],
            isError=True
        )


async def _load_csv(data: str, params: dict) -> ToolResult:
    """Load CSV data."""
    import pandas as pd
    
    if data.startswith("http"):
        df = pd.read_csv(data)
    else:
        df = pd.read_csv(io.StringIO(data))
    
    output = f"## Loaded DataFrame\n\n"
    output += f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n"
    output += f"**Columns:** {', '.join(df.columns.tolist())}\n\n"
    output += f"**Preview:**\n```\n{df.head(10).to_string()}\n```"
    
    return ToolResult(content=[TextContent(text=output)])


async def _load_json(data: str, params: dict) -> ToolResult:
    """Load JSON data."""
    import pandas as pd
    import json
    
    if data.startswith("http"):
        df = pd.read_json(data)
    else:
        json_data = json.loads(data)
        df = pd.DataFrame(json_data)
    
    output = f"## Loaded DataFrame\n\n"
    output += f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n"
    output += f"**Preview:**\n```\n{df.head(10).to_string()}\n```"
    
    return ToolResult(content=[TextContent(text=output)])


async def _describe(data: str, params: dict) -> ToolResult:
    """Describe DataFrame statistics."""
    import pandas as pd
    
    if data.startswith("http"):
        df = pd.read_csv(data)
    else:
        df = pd.read_csv(io.StringIO(data))
    
    output = f"## Data Statistics\n\n"
    output += f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n"
    output += f"**Data Types:**\n```\n{df.dtypes.to_string()}\n```\n\n"
    output += f"**Statistics:**\n```\n{df.describe().to_string()}\n```\n\n"
    output += f"**Missing Values:**\n```\n{df.isnull().sum().to_string()}\n```"
    
    return ToolResult(content=[TextContent(text=output)])


async def _filter(data: str, params: dict) -> ToolResult:
    """Filter DataFrame."""
    import pandas as pd
    
    if data.startswith("http"):
        df = pd.read_csv(data)
    else:
        df = pd.read_csv(io.StringIO(data))
    
    condition = params.get("condition", "")
    if not condition:
        return ToolResult(
            content=[TextContent(text="Error: Filter condition required")],
            isError=True
        )
    
    filtered = df.query(condition)
    
    output = f"## Filtered Results\n\n"
    output += f"**Condition:** `{condition}`\n"
    output += f"**Matched:** {len(filtered)} of {len(df)} rows\n\n"
    output += f"**Results:**\n```\n{filtered.head(50).to_string()}\n```"
    
    return ToolResult(content=[TextContent(text=output)])


async def _aggregate(data: str, params: dict) -> ToolResult:
    """Aggregate DataFrame."""
    import pandas as pd
    
    if data.startswith("http"):
        df = pd.read_csv(data)
    else:
        df = pd.read_csv(io.StringIO(data))
    
    group_by = params.get("group_by", [])
    agg_funcs = params.get("agg", {"*": "count"})
    
    if group_by:
        result = df.groupby(group_by).agg(agg_funcs)
    else:
        result = df.agg(agg_funcs)
    
    output = f"## Aggregation Results\n\n"
    output += f"**Group By:** {group_by or 'None'}\n"
    output += f"**Aggregations:** {agg_funcs}\n\n"
    output += f"**Results:**\n```\n{result.to_string()}\n```"
    
    return ToolResult(content=[TextContent(text=output)])
