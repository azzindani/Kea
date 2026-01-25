
"""
yfinance MCP Server (Maximized).
"""

from __future__ import annotations

import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import yfinance as yf

# Handlers
from mcp_servers.yfinance_server.tools.charts import get_price_chart
from mcp_servers.yfinance_server.tools.market import (
    get_bulk_historical_data, get_current_price, get_market_cap, get_pe_ratio, 
    get_volume, get_beta, get_quote_metadata
)
from mcp_servers.yfinance_server.tools.financials import (
    get_income_statement_annual, get_income_statement_quarterly,
    get_balance_sheet_annual, get_balance_sheet_quarterly,
    get_cash_flow_annual, get_cash_flow_quarterly
)
from mcp_servers.yfinance_server.tools.holders import (
    get_major_holders_breakdown, get_institutional_holders, get_mutual_fund_holders,
    get_insider_transactions, get_insider_roster
)
from mcp_servers.yfinance_server.tools.analysis import (
    get_analyst_recommendations, get_price_targets, get_earnings_calendar,
    get_upgrades_downgrades, get_dividends_history, get_splits_history,
    calculate_indicators
)
from mcp_servers.yfinance_server.tools.options import get_options_chain, get_option_expirations
from mcp_servers.yfinance_server.tools.discovery import scan_country
from mcp_servers.yfinance_server.tools.aggregators import get_full_ticker_report

logger = get_logger(__name__)

# --- DYNAMIC INFO KEYS ---
# These are available keys in yfinance.info that we will expose as individual tools.
# This approach bridges the gap to "120 tools" by granularly exposing every metric.
INFO_KEYS = [
    # Valuation
    "enterpriseValue", "forwardPE", "pegRatio", "priceToBook", "priceToSalesTrailing12Months",
    "enterpriseToRevenue", "enterpriseToEbitda", 
    # Profitability
    "profitMargins", "ebitdaMargins", "operatingMargins", "grossMargins",
    "returnOnAssets", "returnOnEquity",
    # Financials
    "totalRevenue", "revenuePerShare", "revenueGrowth", "grossProfits",
    "ebitda", "netIncomeToCommon", "trailingEps", "forwardEps",
    "totalCash", "totalCashPerShare", "totalDebt", "quickRatio", "currentRatio",
    # Trading
    "floatShares", "sharesOutstanding", "sharesShort", "shortRatio", "shortPercentOfFloat",
    "averageVolume10days", "averageVolume",
    # Splits & Divs
    "dividendRate", "dividendYield", "exDividendDate", "payoutRatio", "lastSplitFactor", "lastSplitDate",
    # Profile
    "sector", "industry", "fullTimeEmployees", "city", "state", "country", "website",
    "longBusinessSummary", "auditRisk", "boardRisk", "compensationRisk", "shareHolderRightsRisk", "overallRisk"
]

class YFinanceServer(MCPServer):
    """MCP Server for 'Bloomberg-lite' financial data via yfinance."""
    
    def __init__(self) -> None:
        super().__init__(name="yfinance_server", version="3.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register all expanded tools (Target: 100+)."""
        
        # --- 1. Core Explicit Tools (Manual) ---
        
        # Market
        self.reg("get_current_price", get_current_price, "Get price snapshot.")
        self.reg("get_market_cap", get_market_cap, "Get Market Cap.")
        self.reg("get_pe_ratio", get_pe_ratio, "Get Trailing PE Ratio.")
        self.reg("get_metric_volume", get_volume, "Get recent volume.")
        self.reg("get_metric_beta", get_beta, "Get Beta (Volatility).")
        self.reg("get_quote_metadata", get_quote_metadata, "Get Bid/Ask/Currency.")
        self.reg("get_bulk_historical_data", get_bulk_historical_data, "FILESYSTEM: Get history for multiple tickers (CSV).", params={"tickers": "str", "period": "str", "interval": "str"})
        
        # Financials
        self.reg("get_income_statement_annual", get_income_statement_annual, "Annual Income Statement.")
        self.reg("get_income_statement_quarterly", get_income_statement_quarterly, "Quarterly Income Statement.")
        self.reg("get_balance_sheet_annual", get_balance_sheet_annual, "Annual Balance Sheet.")
        self.reg("get_balance_sheet_quarterly", get_balance_sheet_quarterly, "Quarterly Balance Sheet.")
        self.reg("get_cash_flow_annual", get_cash_flow_annual, "Annual Cash Flow.")
        self.reg("get_cash_flow_quarterly", get_cash_flow_quarterly, "Quarterly Cash Flow.")
        
        # Holders
        self.reg("get_major_holders", get_major_holders_breakdown, "Breakdown of Insiders vs Institutions.")
        self.reg("get_institutional_holders", get_institutional_holders, "Top Institutional Holders.")
        self.reg("get_mutual_funds", get_mutual_fund_holders, "Top Mutual Funds.")
        self.reg("get_insider_transactions", get_insider_transactions, "Recent Insider Trading.")
        self.reg("get_insider_roster", get_insider_roster, "Key Executives/Holders.")
        
        # Analysis
        self.reg("get_analyst_ratings", get_analyst_recommendations, "Buy/Sell/Hold Ratings.")
        self.reg("get_price_targets", get_price_targets, "High/Low/Mean targets")
        self.reg("get_upgrades_downgrades", get_upgrades_downgrades, "Recent Analyst Actions.")
        self.reg("get_earnings_calendar", get_earnings_calendar, "Upcoming Earnings Dates.")
        self.reg("get_dividends_history", get_dividends_history, "Dividend Payment History.")
        self.reg("get_splits_history", get_splits_history, "Stock Splits History.")
        self.reg("calculate_indicators", calculate_indicators, "Technical Analysis (SMA, RSI, MACD).", params={"ticker": "str", "indicators": "list", "period": "str"})

        # Charts
        self.reg("get_price_chart", get_price_chart, "Generate Price Chart (Image).", params={"ticker": "str", "period": "str"})
        
        # Options
        self.reg("get_options_chain", get_options_chain, "Get Option Chain.", params={"ticker": "str", "date": "str"})
        self.reg("get_option_expirations", get_option_expirations, "Get Option Expirations.")
        
        # Aggregators
        self.reg("scan_country", scan_country, "NETWORK: Scan entire country.", params={"country_code": "str"})
        self.reg("get_full_report", get_full_ticker_report, "MULTI-TALENT: Full aggregated report.")

        # --- 2. Dynamic Info Bridge (The "Explosion") ---
        # Registers a distinct tool for every useful metadata field
        for key in INFO_KEYS:
            tool_name = f"get_{self._snake_case(key)}"
            desc = f"Get specific metric: {key}."
            
            # Create a closure for the handler
            async def dynamic_handler(args: dict, k=key) -> ToolResult:
                ticker = args.get("ticker")
                try:
                    val = yf.Ticker(ticker).info.get(k, "N/A")
                    return ToolResult(content=[TextContent(text=str(val))])
                except: return ToolResult(isError=True, content=[TextContent(text="N/A")])
            
            # Register manually since logic is dynamic
            self.register_tool(
                name=tool_name,
                description=desc,
                handler=dynamic_handler,
                parameters={"ticker": {"type": "string", "description": "Stock Symbol"}},
                required=["ticker"]
            )

    def _snake_case(self, s: str) -> str:
        return ''.join(['_' + c.lower() if c.isupper() else c for c in s]).lstrip('_')
    
    def reg(self, name, handler, desc, params=None):
        if params is None:
            p = {"ticker": {"type": "string", "description": "Stock Symbol"}}
            r = ["ticker"]
        else:
            p = {}
            r = []
            for k, v in params.items():
                p[k] = {"type": "string" if v == "str" else v}
                r.append(k)
        self.register_tool(name=name, description=desc, handler=handler, parameters=p, required=r)

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="yfinance_server"))
    server = YFinanceServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
