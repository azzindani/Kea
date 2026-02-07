
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "asyncpg",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import fs_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("filesystem_server", dependencies=["asyncpg"])

@mcp.tool()
async def fs_init() -> str:
    """INITIALIZES the VFS database schema. [ENTRY]
    
    [RAG Context]
    Idempotent operation to set up the file system.
    """
    return await fs_ops.init_db()

@mcp.tool()
async def fs_ls(path: str = "/") -> str:
    """LISTS files and folders in a directory. [DATA]
    
    [RAG Context]
    Returns a list of file names and metadata.
    """
    return await fs_ops.list_files(path)

@mcp.tool()
async def fs_mkdir(path: str) -> str:
    """CREATES a new folder. [ACTION]
    
    [RAG Context]
    Creates directory recursively if needed.
    """
    return await fs_ops.make_directory(path)

@mcp.tool()
async def fs_write(path: str, content: str, description: str = "") -> str:
    """WRITES content to a file. [ACTION]
    
    [RAG Context]
    Supports Virtual & Physical writes.
    """
    return await fs_ops.write_file(path, content, description)

@mcp.tool()
async def fs_read(path: str) -> str:
    """READS content of a file. [DATA]
    
    [RAG Context]
    """
    return await fs_ops.read_file(path)

if __name__ == "__main__":
    mcp.run()