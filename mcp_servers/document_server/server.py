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


from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from tools import pdf, word, excel, html, json_tool
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("document_server", dependencies=["httpx", "pymupdf", "python-docx", "pandas", "bs4"])

@mcp.tool()
async def pdf_parser(url: str, pages: str = "all", extract_tables: bool = False) -> str:
    """
    Extract text from PDF file.
    pages: 'all', '1-5', '1,3,5'
    """
    return await pdf.parse_pdf(url, pages, extract_tables)

@mcp.tool()
async def docx_parser(url: str) -> str:
    """Extract text from Word documents."""
    return await word.parse_docx(url)

@mcp.tool()
async def xlsx_parser(url: str, sheet_name: str = None, preview_rows: int = 10) -> str:
    """Parse Excel spreadsheets."""
    return await excel.parse_excel(url, sheet_name, preview_rows)

@mcp.tool()
async def html_parser(url: str, extract: str = "text", selector: str = None) -> str:
    """
    Parse HTML and extract structured content.
    extract: 'text', 'links', 'tables', 'images'
    """
    return await html.parse_html(url, extract, selector)

@mcp.tool()
async def json_parser(url: str, flatten: bool = False, path: str = None) -> str:
    """
    Parse and flatten JSON data.
    """
    return await json_tool.parse_json(url, flatten, path)

if __name__ == "__main__":
    mcp.run()

