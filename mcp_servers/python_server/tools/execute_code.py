"""
Execute Code Tool.

Sandboxed Python execution with restricted imports.
"""

from __future__ import annotations

import io
import sys
import asyncio
from contextlib import redirect_stdout, redirect_stderr
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)

# Allowed imports for sandboxed execution
ALLOWED_IMPORTS = {
    "math", "statistics", "datetime", "json", "re", "collections",
    "itertools", "functools", "operator", "random", "string",
    "pandas", "numpy", "duckdb",
}


async def execute_code_tool(arguments: dict) -> ToolResult:
    """
    Execute Python code in sandboxed environment.
    
    Args:
        arguments: Tool arguments containing:
            - code: Python code to execute
            - timeout: Execution timeout (default 30s)
    
    Returns:
        ToolResult with stdout, variables, and any errors
    """
    code = arguments.get("code", "")
    timeout = arguments.get("timeout", 30)
    
    if not code:
        return ToolResult(
            content=[TextContent(text="Error: Code is required")],
            isError=True
        )
    
    # Basic security check
    forbidden = ["os.system", "subprocess", "eval(", "exec(", "__import__", "open("]
    for pattern in forbidden:
        if pattern in code:
            return ToolResult(
                content=[TextContent(text=f"Error: Forbidden operation: {pattern}")],
                isError=True
            )
    
    try:
        result = await asyncio.wait_for(
            _execute_in_sandbox(code),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        return ToolResult(
            content=[TextContent(text=f"Error: Execution timed out after {timeout}s")],
            isError=True
        )
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return ToolResult(
            content=[TextContent(text=f"Error: {str(e)}")],
            isError=True
        )


async def _execute_in_sandbox(code: str) -> ToolResult:
    """Execute code in a restricted environment."""
    
    # Capture output
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    # Create restricted globals
    restricted_globals: dict[str, Any] = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "type": type,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
        }
    }
    
    # Add allowed imports
    try:
        import pandas as pd
        import numpy as np
        import duckdb
        
        restricted_globals["pd"] = pd
        restricted_globals["pandas"] = pd
        restricted_globals["np"] = np
        restricted_globals["numpy"] = np
        restricted_globals["duckdb"] = duckdb
    except ImportError:
        pass
    
    local_vars: dict[str, Any] = {}
    
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code, restricted_globals, local_vars)
        
        # Build output
        output_parts = []
        
        stdout_content = stdout_buffer.getvalue()
        if stdout_content:
            output_parts.append(f"## Output\n```\n{stdout_content}\n```")
        
        stderr_content = stderr_buffer.getvalue()
        if stderr_content:
            output_parts.append(f"## Warnings\n```\n{stderr_content}\n```")
        
        # Extract interesting variables
        result_vars = {}
        for name, value in local_vars.items():
            if not name.startswith("_"):
                try:
                    # Convert to string representation
                    if hasattr(value, "to_string"):
                        result_vars[name] = value.to_string()[:2000]
                    elif hasattr(value, "__len__") and len(value) > 100:
                        result_vars[name] = f"<{type(value).__name__} with {len(value)} items>"
                    else:
                        result_vars[name] = str(value)[:1000]
                except Exception:
                    result_vars[name] = f"<{type(value).__name__}>"
        
        if result_vars:
            vars_str = "\n".join(f"- {k}: {v}" for k, v in result_vars.items())
            output_parts.append(f"## Variables\n{vars_str}")
        
        if not output_parts:
            output_parts.append("Code executed successfully (no output)")
        
        return ToolResult(
            content=[TextContent(text="\n\n".join(output_parts))]
        )
        
    except Exception as e:
        return ToolResult(
            content=[TextContent(text=f"Execution Error: {type(e).__name__}: {str(e)}")],
            isError=True
        )
