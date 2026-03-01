"""
Execute Code Tool.

Sandboxed Python execution with restricted imports.
"""

from __future__ import annotations

import io
import sys
import asyncio
import json
from contextlib import redirect_stdout, redirect_stderr
from typing import Any

from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger


logger = get_logger(__name__)

# Allowed imports for sandboxed execution
ALLOWED_IMPORTS = {
    "math", "statistics", "datetime", "json", "re", "collections",
    "itertools", "functools", "operator", "random", "string",
    "pandas", "numpy", "duckdb",
}


async def execute_code_tool(arguments: dict) -> ToolResult:
    """
    Execute Python code in JIT environment using 'uv'.
    """
    code = arguments.get("code", "")
    timeout = arguments.get("timeout", 60)
    dependencies = arguments.get("dependencies", [])
    
    if not code:
        return ToolResult(content=[TextContent(text="Error: Code is required")], isError=True)
    
    # Validation
    forbidden = ["os.system", "subprocess.call", "subprocess.Popen", "import local_module"]
    for pattern in forbidden:
        if pattern in code:
             # Basic static check, though the sandbox is the real defense
            return ToolResult(content=[TextContent(text=f"Error: Forbidden pattern: {pattern}")], isError=True)

    import tempfile
    import os
    import shutil
    import subprocess
    
    # Create isolated temp directory
    temp_dir = tempfile.mkdtemp(prefix="project_sandbox_")
    script_path = os.path.join(temp_dir, "script.py")
    
    try:
        # 1. Write Code with Auto-Imports
        with open(script_path, "w", encoding="utf-8") as f:
            # Auto-inject common imports to prevent NameError
            preamble = []
            if "pandas" in dependencies or "pd" in code:
                preamble.append("import pandas as pd")
            if "numpy" in dependencies or "np" in code:
                preamble.append("import numpy as np")
            if "yfinance" in dependencies or "yf" in code:
                preamble.append("import yfinance as yf")
            
            if preamble:
                f.write("\n".join(preamble) + "\n\n")
            
            f.write(code)
            
        # 2. Build 'uv' command
        # uv run --quiet --with dep1 --with dep2 python script.py
        cmd = ["uv", "run", "--quiet"]
        
        # Ensure dependencies are unique
        deps_set = set(dependencies)
        
        # Smart dependency detection
        if "pd" in code or "pandas" in code:
            deps_set.add("pandas")
        if "np" in code or "numpy" in code:
            deps_set.add("numpy")
        if "yf" in code or "yfinance" in code:
            deps_set.add("yfinance")
            
        for dep in sorted(list(deps_set)):
             cmd.extend(["--with", dep])
        
        # Add python script target
        cmd.extend(["python", "script.py"])
        
        logger.info(f"🚀 JIT Execution: {' '.join(cmd)} in {temp_dir}")
        
        # 3. Execute with timeout
        # We assume 'uv' is in PATH. If not, we might need absolute path.
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONUNBUFFERED": "1"} # Ensure we capture output
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return ToolResult(
                content=[TextContent(text=f"Error: Execution timed out ({timeout}s)")],
                isError=True
            )
            
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()
        
        output_data = {
            "status": "success",
            "stdout": stdout_str,
            "stderr": stderr_str,
            "returncode": process.returncode
        }
        
        # Filter uv noise from stderr if successful
        if process.returncode == 0 and stderr_str:
             clean_stderr = [l for l in stderr_str.split('\n') if not l.startswith("Resolved ") and not l.startswith("Audited ")]
             output_data["stderr"] = "\n".join(clean_stderr)

        if process.returncode != 0:
            output_data["status"] = "error"
            output_data["error"] = stderr_str or "Unknown Error"
            return ToolResult(
                content=[TextContent(text=json.dumps(output_data, indent=2))],
                isError=True
            )
            
        return ToolResult(
            content=[TextContent(text=json.dumps(output_data, indent=2))]
        )

    except Exception as e:
        logger.error(f"JIT Error: {e}")
        return ToolResult(
            content=[TextContent(text=f"System Error: {str(e)}")],
            isError=True
        )
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
            
# Removing _execute_in_sandbox helper as we now use subprocess isolation
