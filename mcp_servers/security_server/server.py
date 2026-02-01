
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "httpx",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import security_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("security_server", dependencies=["httpx"])

@mcp.tool()
async def url_scanner(url: str, deep_scan: bool = False) -> str:
    """Check URL for potential security threats."""
    return await security_ops.url_scanner(url, deep_scan)

@mcp.tool()
async def content_sanitizer(content: str, allow_html: bool = False) -> str:
    """Sanitize HTML/text content to remove malicious elements."""
    return await security_ops.content_sanitizer(content, allow_html)

@mcp.tool()
async def file_hash_check(file_path: str = None, content: str = "", algorithm: str = "sha256") -> str:
    """Calculate file hash and check against known threats."""
    return await security_ops.file_hash_check(file_path, content, algorithm)

@mcp.tool()
async def domain_reputation(domain: str) -> str:
    """Check domain reputation and safety."""
    return await security_ops.domain_reputation(domain)

@mcp.tool()
async def safe_download(url: str, max_size_mb: int = 10, allowed_types: list = None) -> str:
    """Download file with safety checks."""
    return await security_ops.safe_download(url, max_size_mb, allowed_types)

@mcp.tool()
async def code_safety_check(code: str, language: str = "python") -> str:
    """Check code for potentially dangerous operations."""
    return await security_ops.code_safety_check(code, language)

if __name__ == "__main__":
    mcp.run()