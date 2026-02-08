
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
from mcp_servers.security_server.tools import security_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("security_server", dependencies=["httpx"])

@mcp.tool()
async def url_scanner(url: str, deep_scan: bool = False) -> str:
    """SCANS URL. [ACTION]
    
    [RAG Context]
    Check URL for potential security threats.
    Returns scan report.
    """
    return await security_ops.url_scanner(url, deep_scan)

@mcp.tool()
async def content_sanitizer(content: str, allow_html: bool = False) -> str:
    """SANITIZES content. [ACTION]
    
    [RAG Context]
    Sanitize HTML/text content to remove malicious elements.
    Returns cleaned content.
    """
    return await security_ops.content_sanitizer(content, allow_html)

@mcp.tool()
async def file_hash_check(file_path: str = None, content: str = "", algorithm: str = "sha256") -> str:
    """CHECKS file hash. [ACTION]
    
    [RAG Context]
    Calculate file hash and check against known threats.
    Returns report string.
    """
    return await security_ops.file_hash_check(file_path, content, algorithm)

@mcp.tool()
async def domain_reputation(domain: str) -> str:
    """CHECKS reputation. [ACTION]
    
    [RAG Context]
    Check domain reputation and safety.
    Returns report string.
    """
    return await security_ops.domain_reputation(domain)

@mcp.tool()
async def safe_download(url: str, max_size_mb: int = 10, allowed_types: list = None) -> str:
    """DOWNLOADS safely. [ACTION]
    
    [RAG Context]
    Download file with safety checks (size, type).
    Returns output path.
    """
    return await security_ops.safe_download(url, max_size_mb, allowed_types)

@mcp.tool()
async def code_safety_check(code: str, language: str = "python") -> str:
    """CHECKS code safety. [ACTION]
    
    [RAG Context]
    Check code for potentially dangerous operations.
    Returns analysis report.
    """
    return await security_ops.code_safety_check(code, language)

if __name__ == "__main__":
    mcp.run()