
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

async def generate_mcp_stub(package_name: str, functions: list[str] = None, server_name: str = None) -> ToolResult:
    """Generate MCP tool stub code for a package."""
    if functions is None:
        functions = ["main_function"]
        
    if server_name is None:
        server_name = f"{package_name.replace('-', '_')}_server"
    
    result = f"# 🛠️ MCP Stub for: {package_name}\n\n"
    
    # Generate template code
    code = f'''"""
{package_name.title()} MCP Server.

Auto-generated stub - customize as needed.
"""

from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("{server_name}", dependencies=["{package_name}"])

'''
    
    for func in functions:
        code += f'''@mcp.tool()
def {func}(input_arg: str) -> str:
    """TODO: Describe {func}."""
    # import {package_name.replace('-', '_')}
    return f"Processed {{input_arg}}"

'''

    code += '''
if __name__ == "__main__":
    mcp.run()
'''
    
    result += f"## Generated Code\n\n```python\n{code}\n```\n\n"
    result += f"**Save to**: `mcp_servers/{server_name}/server.py`\n"
    result += f"**Install dep**: `pip install {package_name}`\n"
    
    return ToolResult(content=[TextContent(text=result)])
