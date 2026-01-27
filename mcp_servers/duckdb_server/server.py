from mcp.server.fastmcp import FastMCP
from mcp_servers.duckdb_server.tools import core_ops
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("duckdb_server", dependencies=["pandas", "duckdb", "pyarrow"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def connect_db(path: str = "kea_data.duckdb") -> str: return core_ops.connect_db(path)
@mcp.tool()
def get_version() -> str: return core_ops.get_version()
@mcp.tool()
def list_extensions() -> str: return core_ops.list_extensions()
@mcp.tool()
def install_extension(name: str) -> str: return core_ops.install_extension(name)
@mcp.tool()
def load_extension(name: str) -> str: return core_ops.load_extension(name)
@mcp.tool()
def get_current_db_path() -> str: return core_ops.get_current_db_path()
@mcp.tool()
def close_connection() -> str: return core_ops.close_connection()
@mcp.tool()
def set_config(key: str, value: str) -> str: return core_ops.set_config(key, value)

if __name__ == "__main__":
    mcp.run()
