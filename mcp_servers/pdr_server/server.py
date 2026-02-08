from __future__ import annotations

import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import asyncio
from mcp.server.fastmcp import FastMCP

# --- PATCH: Fix pandas-datareader compatibility ---
# pandas-datareader uses an old signature for deprecate_kwarg.
# We patch it to prevent TypeError on import.
try:
    import pandas.util._decorators
    def mock_deprecate_kwarg(old_arg_name, new_arg_name, mapping=None, stacklevel=2):
        def decorator(func):
            return func
        return decorator
    pandas.util._decorators.deprecate_kwarg = mock_deprecate_kwarg
except ImportError:
    pass
# --------------------------------------------------

# Tools - use aliased imports to avoid naming collisions
from mcp_servers.pdr_server.tools import famafrench, market_global, dashboards, market_symbols, central_bank, commercial
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("pdr_server", dependencies=["pandas_datareader", "pandas"])

# --- 1. ACADEMIC ENGINE (Fama-French) ---

@mcp.tool()
async def get_fama_french_data(dataset_name: str, start_date: str = None, end_date: str = None) -> str:
    """FETCHES Fama-French data. [ACTION]
    
    [RAG Context]
    ACADEMIC: Get Fama-French Data by Code.
    Common Codes: 'F-F_Research_Data_Factors', 'F-F_Momentum_Factor', '5_Industry_Portfolios'.
    Returns JSON string.
    """
    return await famafrench.get_fama_french_data(dataset_name, start_date, end_date)

# --- 2. MARKET ENGINE (Stooq, TSP) ---

@mcp.tool()
async def get_stooq_data(symbols: list[str], start_date: str = None) -> str:
    """FETCHES Stooq data. [ACTION]
    
    [RAG Context]
    MARKET: Stooq Data (Indices, Bonds, Commodities).
    Returns JSON string.
    """
    return await market_global.get_stooq_data(symbols, start_date)

@mcp.tool()
async def get_tsp_fund_data() -> str:
    """FETCHES TSP fund data. [ACTION]
    
    [RAG Context]
    INSTITUTION: Thrift Savings Plan (TSP) Funds.
    Returns JSON string.
    """
    return await market_global.get_tsp_fund_data()

@mcp.tool()
async def get_moex_data(symbols: list[str], start_date: str = None) -> str:
    """FETCHES Moscow Exchange data. [ACTION]
    
    [RAG Context]
    MARKET: Moscow Exchange Data.
    Returns JSON string.
    """
    return await market_global.get_moex_data(symbols, start_date)

# --- 3. DASHBOARDS ---

@mcp.tool()
async def get_factor_dashboard() -> str:
    """FETCHES US Factors dashboard. [ACTION]
    
    [RAG Context]
    DASHBOARD: US Factors (5-Factor + Momentum).
    Returns JSON string.
    """
    return await dashboards.get_factor_dashboard()

@mcp.tool()
async def get_global_factors_dashboard() -> str:
    """FETCHES Global Factors dashboard. [ACTION]
    
    [RAG Context]
    DASHBOARD: Global Factors (Regions).
    Returns JSON string.
    """
    return await dashboards.get_global_factors_dashboard()

@mcp.tool()
async def get_industry_health_dashboard() -> str:
    """FETCHES Industry Health dashboard. [ACTION]
    
    [RAG Context]
    DASHBOARD: 49 Industry Sectors Health.
    Returns JSON string.
    """
    return await dashboards.get_industry_health_dashboard()

@mcp.tool()
async def get_liquidity_dashboard() -> str:
    """FETCHES Liquidity dashboard. [ACTION]
    
    [RAG Context]
    DASHBOARD: Market Liquidity Factors.
    Returns JSON string.
    """
    return await dashboards.get_liquidity_dashboard()

# --- 4. DISCOVERY & CENTRAL BANK ---

@mcp.tool()
async def get_nasdaq_symbol_list(query: str = None) -> str:
    """SEARCHES Nasdaq symbols. [ACTION]
    
    [RAG Context]
    DISCOVERY: Search Nasdaq/NYSE Symbols.
    Returns JSON string.
    """
    return await market_symbols.get_nasdaq_symbol_list(query)

@mcp.tool()
async def get_bank_of_canada_data(symbols: list[str] = None, start_date: str = None) -> str:
    """FETCHES Bank of Canada data. [ACTION]
    
    [RAG Context]
    MACRO: Bank of Canada Rates/FX.
    Returns JSON string.
    """
    return await central_bank.get_bank_of_canada_data(symbols, start_date)

# --- 5. COMMERCIAL ---

@mcp.tool()
async def get_tiingo_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """FETCHES Tiingo data. [ACTION]
    
    [RAG Context]
    COMMERCIAL: Tiingo Data (Req API Key).
    Returns JSON string.
    """
    return await commercial.get_tiingo_data(symbols, api_key, start_date)

@mcp.tool()
async def get_alphavantage_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """FETCHES AlphaVantage data. [ACTION]
    
    [RAG Context]
    COMMERCIAL: AlphaVantage Data (Req API Key).
    Returns JSON string.
    """
    return await commercial.get_alphavantage_data(symbols, api_key, start_date)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PdrServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
