# /// script
# dependencies = [
#   "httpx",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
from tools import regulatory_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("regulatory_server", dependencies=["httpx"])

@mcp.tool()
async def edgar_search(company: str, filing_type: str = "", date_from: str = None, date_to: str = None) -> str:
    """Search SEC EDGAR for company filings (10-K, 10-Q, 8-K, etc.)."""
    return await regulatory_ops.edgar_search(company, filing_type, date_from, date_to)

@mcp.tool()
async def edgar_filing_content(accession_number: str, section: str = "all") -> str:
    """Get content of a specific SEC filing."""
    return await regulatory_ops.edgar_filing_content(accession_number, section)

@mcp.tool()
async def ecfr_search(query: str, title: int = None) -> str:
    """Search eCFR (Code of Federal Regulations)."""
    return await regulatory_ops.ecfr_search(query, title)

@mcp.tool()
async def federal_register_search(query: str, document_type: str = None, agency: str = None) -> str:
    """Search Federal Register for new rules and notices."""
    return await regulatory_ops.federal_register_search(query, document_type, agency)

@mcp.tool()
async def wto_data(indicator: str, country: str = None, year: int = None) -> str:
    """Get WTO trade statistics and agreements."""
    return await regulatory_ops.wto_data(indicator, country, year)

@mcp.tool()
async def imf_data(indicator: str, country: str = None, year: str = None) -> str:
    """Get IMF economic data and forecasts."""
    return await regulatory_ops.imf_data(indicator, country, year)

if __name__ == "__main__":
    mcp.run()
