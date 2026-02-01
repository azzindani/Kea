import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))


from __future__ import annotations
import asyncio
from mcp.server.fastmcp import FastMCP

# Tools
from tools.famafrench import get_fama_french_data, get_ff_map
from tools.market_global import get_stooq_data, get_tsp_fund_data, get_moex_data
from tools.dashboards import (
    get_factor_dashboard, get_global_factors_dashboard, get_industry_health_dashboard, get_liquidity_dashboard
)
from tools.market_symbols import get_nasdaq_symbol_list
from tools.central_bank import get_bank_of_canada_data
from tools.commercial import get_tiingo_data, get_alphavantage_data

mcp = FastMCP("pdr_server", dependencies=["pandas_datareader", "pandas"])

# --- 1. ACADEMIC ENGINE (Fama-French) ---

@mcp.tool()
async def get_fama_french_data(dataset_name: str, start_date: str = None, end_date: str = None) -> str:
    """
    ACADEMIC: Get Fama-French Data by Code.
    Common Codes: 'F-F_Research_Data_Factors', 'F-F_Momentum_Factor', '5_Industry_Portfolios'.
    """
    return await get_fama_french_data(dataset_name, start_date, end_date)

# Register aliases for popular FF datasets directly?
# We can register the same function with different names if we want shortcuts.
# But providing the map in description is often enough.

# --- 2. MARKET ENGINE (Stooq, TSP) ---

@mcp.tool()
async def get_stooq_data(symbols: list[str], start_date: str = None) -> str:
    """MARKET: Stooq Data (Indices, Bonds, Commodities)."""
    return await get_stooq_data(symbols, start_date)

@mcp.tool()
async def get_tsp_fund_data() -> str:
    """INSTITUTION: Thrift Savings Plan (TSP) Funds."""
    return await get_tsp_fund_data()

@mcp.tool()
async def get_moex_data(symbols: list[str], start_date: str = None) -> str:
    """MARKET: Moscow Exchange Data."""
    return await get_moex_data(symbols, start_date)

# --- 3. DASHBOARDS ---

@mcp.tool()
async def get_factor_dashboard() -> str:
    """DASHBOARD: US Factors (5-Factor + Momentum)."""
    return await get_factor_dashboard()

@mcp.tool()
async def get_global_factors_dashboard() -> str:
    """DASHBOARD: Global Factors (Regions)."""
    return await get_global_factors_dashboard()

@mcp.tool()
async def get_industry_health_dashboard() -> str:
    """DASHBOARD: 49 Industry Sectors Health."""
    return await get_industry_health_dashboard()

@mcp.tool()
async def get_liquidity_dashboard() -> str:
    """DASHBOARD: Market Liquidity Factors."""
    return await get_liquidity_dashboard()

# --- 4. DISCOVERY & CENTRAL BANK ---

@mcp.tool()
async def get_nasdaq_symbol_list(query: str = None) -> str:
    """DISCOVERY: Search Nasdaq/NYSE Symbols."""
    return await get_nasdaq_symbol_list(query)

@mcp.tool()
async def get_bank_of_canada_data(symbols: list[str] = None, start_date: str = None) -> str:
    """MACRO: Bank of Canada Rates/FX."""
    return await get_bank_of_canada_data(symbols, start_date)

# --- 5. COMMERCIAL ---

@mcp.tool()
async def get_tiingo_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """COMMERCIAL: Tiingo Data (Req API Key)."""
    return await get_tiingo_data(symbols, api_key, start_date)

@mcp.tool()
async def get_alphavantage_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """COMMERCIAL: AlphaVantage Data (Req API Key)."""
    return await get_alphavantage_data(symbols, api_key, start_date)


if __name__ == "__main__":
    mcp.run()