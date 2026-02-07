
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "fredapi",
#   "mcp",
#   "pandas",
#   "structlog",
#   "wbgapi",
#   "yfinance",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import fetchers
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("data_sources_server", dependencies=["yfinance", "fredapi", "wbgapi", "pandas"])

@mcp.tool()
async def yfinance_fetch(symbol: str, period: str = "1mo", interval: str = "1d", data_type: str = "history") -> str:
    """FETCHES Yahoo Finance data. [ACTION]
    
    [RAG Context]
    Fetch stock/financial data from Yahoo Finance.
    Returns data string.
    """
    return await fetchers.fetch_yfinance(symbol, period, interval, data_type)

@mcp.tool()
async def fred_fetch(series_id: str, start_date: str = None, end_date: str = None) -> str:
    """FETCHES FRED data. [ACTION]
    
    [RAG Context]
    Fetch economic data from FRED (Federal Reserve Economic Data).
    Returns data string.
    """
    return await fetchers.fetch_fred(series_id, start_date, end_date)

@mcp.tool()
async def world_bank_fetch(indicator: str, country: str = "all", start_year: int = None, end_year: int = None) -> str:
    """FETCHES World Bank data. [ACTION]
    
    [RAG Context]
    Fetch development indicators from World Bank.
    Returns data string.
    """
    return await fetchers.fetch_world_bank(indicator, country, start_year, end_year)

@mcp.tool()
async def csv_fetch(url: str, preview_rows: int = 5) -> str:
    """FETCHES CSV data. [ACTION]
    
    [RAG Context]
    Fetch CSV data from URL and return as DataFrame info.
    Returns data summary.
    """
    return await fetchers.fetch_csv(url, preview_rows)

if __name__ == "__main__":
    mcp.run()