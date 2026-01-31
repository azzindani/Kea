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
    """
    Fetch stock/financial data from Yahoo Finance.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    data_type: history, info, financials, balance_sheet, cashflow
    """
    return await fetchers.fetch_yfinance(symbol, period, interval, data_type)

@mcp.tool()
async def fred_fetch(series_id: str, start_date: str = None, end_date: str = None) -> str:
    """Fetch economic data from FRED (Federal Reserve Economic Data)."""
    return await fetchers.fetch_fred(series_id, start_date, end_date)

@mcp.tool()
async def world_bank_fetch(indicator: str, country: str = "all", start_year: int = None, end_year: int = None) -> str:
    """
    Fetch development indicators from World Bank.
    indicator: e.g. NY.GDP.MKTP.CD
    """
    return await fetchers.fetch_world_bank(indicator, country, start_year, end_year)

@mcp.tool()
async def csv_fetch(url: str, preview_rows: int = 5) -> str:
    """Fetch CSV data from URL and return as DataFrame info."""
    return await fetchers.fetch_csv(url, preview_rows)

if __name__ == "__main__":
    mcp.run()