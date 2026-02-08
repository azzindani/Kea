from __future__ import annotations

import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "bs4",
#   "httpx",
#   "mcp",
#   "pandas",
#   "pymupdf",
#   "python-docx",
#   "structlog",
# ]
# ///
from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.document_server.tools import pdf, word, excel, html, json_tool
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("document_server", dependencies=["httpx", "pymupdf", "python-docx", "pandas", "bs4"])

@mcp.tool()
async def pdf_parser(url: str, pages: str = "all", extract_tables: bool = False) -> str:
    """EXTRACTS text/tables from PDF. [DATA]
    
    [RAG Context]
    Args:
        pages: 'all', '1-5', '1,3,5'
    """
    return await pdf.parse_pdf(url, pages, extract_tables)

@mcp.tool()
async def docx_parser(url: str) -> str:
    """EXTRACTS text from Word docs. [DATA]
    
    [RAG Context]
    Preserves structure where possible.
    """
    return await word.parse_docx(url)

@mcp.tool()
async def xlsx_parser(url: str, sheet_name: str = None, preview_rows: int = 10) -> str:
    """EXTRACTS data from Excel sheets. [DATA]
    
    [RAG Context]
    Returns CSV or JSON representation.
    """
    return await excel.parse_excel(url, sheet_name, preview_rows)

@mcp.tool()
async def html_parser(url: str, extract: str = "text", selector: str = None) -> str:
    """EXTRACTS content from HTML. [DATA]
    
    [RAG Context]
    Args:
        extract: 'text', 'links', 'tables', 'images'
        selector: CSS selector
    """
    return await html.parse_html(url, extract, selector)

@mcp.tool()
async def json_parser(url: str, flatten: bool = False, path: str = None) -> str:
    """PARSES and FLATTENS JSON data. [DATA]
    
    [RAG Context]
    """
    return await json_tool.parse_json(url, flatten, path)

if __name__ == "__main__":
    mcp.run()
