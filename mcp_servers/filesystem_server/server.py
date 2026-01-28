
from mcp.server.fastmcp import FastMCP
from mcp_servers.filesystem_server.tools import fs_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("filesystem_server", dependencies=["asyncpg"])

@mcp.tool()
async def fs_init() -> str:
    """Initialize the VFS database schema (Idempotent)."""
    return await fs_ops.init_db()

@mcp.tool()
async def fs_ls(path: str = "/") -> str:
    """List files and folders in a directory."""
    return await fs_ops.list_files(path)

@mcp.tool()
async def fs_mkdir(path: str) -> str:
    """Create a new folder."""
    return await fs_ops.make_directory(path)

@mcp.tool()
async def fs_write(path: str, content: str, description: str = "") -> str:
    """Write content to a file (Virtual & Physical)."""
    return await fs_ops.write_file(path, content, description)

@mcp.tool()
async def fs_read(path: str) -> str:
    """Read content of a file."""
    return await fs_ops.read_file(path)

if __name__ == "__main__":
    mcp.run()
