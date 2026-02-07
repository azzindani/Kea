import sys
import os
from pathlib import Path
from mcp import StdioServerParameters

def get_server_params(server_name: str, extra_dependencies: list[str] = None):
    """
    Get StdioServerParameters for a specific server.
    
    Args:
        server_name (str): Name of the server directory (e.g., 'yfinance_server')
        extra_dependencies (list): List of PyPI packages to install via `uv run --with`
    
    Returns:
        StdioServerParameters: Configured parameters to spawn the server.
    """
    # Default dependencies usually needed
    deps = ["mcp", "structlog"]
    if extra_dependencies:
        deps.extend(extra_dependencies)
        
    # Construct paths
    # Assuming we are in root/tests/mcp/ or similar, we need to find root/mcp_servers/
    # Best to use relative path capabilities or env vars if available.
    # Here we assume cwd is project root (standard for pytest)
    
    server_script = os.path.abspath(f"mcp_servers/{server_name}/server.py")
    
    # Verify file exists
    if not os.path.exists(server_script):
        raise FileNotFoundError(f"Server script not found at: {server_script}")
        
    args = ["run"]
    for dep in deps:
        args.extend(["--with", dep])
        
    args.extend(["python", server_script])
    
    return StdioServerParameters(
        command="uv",
        args=args,
        env=os.environ.copy()
    )
