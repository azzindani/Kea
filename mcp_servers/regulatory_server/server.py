
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


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.regulatory_server.tools import regulatory_ops
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("regulatory_server", dependencies=["httpx"])

@mcp.tool()
async def edgar_search(company: str, filing_type: str = "", date_from: str = None, date_to: str = None) -> str:
    """SEARCHES EDGAR. [ACTION]
    
    [RAG Context]
    Search SEC EDGAR for company filings (10-K, 10-Q, 8-K, etc.).
    Returns filing list.
    """
    return await regulatory_ops.edgar_search(company, filing_type, date_from, date_to)

@mcp.tool()
async def edgar_filing_content(accession_number: str, section: str = "all") -> str:
    """FETCHES filing content. [ACTION]
    
    [RAG Context]
    Get content of a specific SEC filing.
    Returns filing text.
    """
    return await regulatory_ops.edgar_filing_content(accession_number, section)

@mcp.tool()
async def ecfr_search(query: str, title: int = None) -> str:
    """SEARCHES eCFR. [ACTION]
    
    [RAG Context]
    Search eCFR (Code of Federal Regulations).
    Returns regulation text.
    """
    return await regulatory_ops.ecfr_search(query, title)

@mcp.tool()
async def federal_register_search(query: str, document_type: str = None, agency: str = None) -> str:
    """SEARCHES Federal Register. [ACTION]
    
    [RAG Context]
    Search Federal Register for new rules and notices.
    Returns results string.
    """
    return await regulatory_ops.federal_register_search(query, document_type, agency)

@mcp.tool()
async def wto_data(indicator: str, country: str = None, year: int = None) -> str:
    """FETCHES WTO data. [ACTION]
    
    [RAG Context]
    Get WTO trade statistics and agreements.
    Returns data string.
    """
    return await regulatory_ops.wto_data(indicator, country, year)

@mcp.tool()
async def imf_data(indicator: str, country: str = None, year: str = None) -> str:
    """FETCHES IMF data. [ACTION]
    
    [RAG Context]
    Get IMF economic data and forecasts.
    Returns data string.
    """
    return await regulatory_ops.imf_data(indicator, country, year)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class RegulatoryServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

