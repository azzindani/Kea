
from yahooquery import Ticker
import pandas as pd
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import json

logger = get_logger(__name__)

class SmartTicker:
    """
    Wrapper for yahooquery.Ticker to handle bulk requests safely.
    Auto-converts complex DataFrames to Markdown.
    """
    def __init__(self, symbols, asynchronous=True):
        # Ensure symbols is a list or string
        if isinstance(symbols, str):
            self.symbols = [s.strip() for s in symbols.split()]
        else:
            self.symbols = symbols
        
        # YahooQuery Ticker init
        self.yq = Ticker(self.symbols, asynchronous=asynchronous)

    def get_module(self, module_name):
        try:
            # Call the property (e.g., self.yq.asset_profile)
            data = getattr(self.yq, module_name)
            
            # Data is usually a dict or DataFrame
            if isinstance(data, pd.DataFrame):
                # Clean up DataFrame for LLM
                return data.to_markdown()
            elif isinstance(data, dict):
                # Valid JSON string
                return json.dumps(data, indent=2, default=str)
            else:
                return str(data)
        except Exception as e:
            logger.error(f"Error fetching {module_name} for {self.symbols}: {e}")
            return f"Error: {str(e)}"

    def get_finance(self, module_name, freq="a"):
        """
        Fetch financials (balance_sheet, cash_flow, income_statement)
        frequency: 'a' (annual) or 'q' (quarterly)
        """
        try:
            # yahooquery uses keys like 'q' or 'a' for frequency in arguments sometimes, 
            # but for properties like balance_sheet, it returns a df.
            # Actually yahooquery separates them: balance_sheet(frequency='q')
            
            method = getattr(self.yq, module_name)
            # Check if it's a method (callable) or property
            if callable(method):
                data = method(frequency=freq)
            else:
                data = method
                
            if isinstance(data, pd.DataFrame):
                return data.to_markdown()
            elif isinstance(data, dict):
                return json.dumps(data, indent=2, default=str)
            return str(data)
        except Exception as e:
            logger.error(f"Finance error {module_name}: {e}")
            return f"Error: {str(e)}"

    def get_options(self):
        try:
            # option_chain is a property in some versions, method in others?
            # In yahooquery 2.0+, it's a property `option_chain` that returns a DataFrame 
            # BUT efficient use usually involves specifying expiration. 
            # Ticker.option_chain is a DataFrame with MultiIndex.
            
            df = self.yq.option_chain
            if isinstance(df, pd.DataFrame):
                # Only head 100 to prevent massive overflow if not filtered
                return df.head(100).to_markdown()
            return str(df)
        except Exception as e:
            logger.error(f"Options error: {e}")
            return f"Error: {e}"

# --- GENERIC HANDLER FOR ALL MODULES ---

async def generic_ticker_handler(arguments: dict, module_name: str) -> ToolResult:
    """
    Generic handler for all Ticker attributes.
    Args:
        tickers (list[str] | str): List of symbols or space-separated string.
    """
    tickers = arguments.get("tickers")
    if not tickers:
        return ToolResult(isError=True, content=[TextContent(text="No tickers provided")])
    
    try:
        st = SmartTicker(tickers)
        result = st.get_module(module_name)
        
        # Add summary header
        count = len(tickers) if isinstance(tickers, list) else len(tickers.split())
        header = f"### Bulk Data: {module_name} ({count} tickers)\n\n"
        
        return ToolResult(content=[TextContent(text=header + result)])
    except Exception as e:
        logger.error(f"Handler error for {module_name}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_bulk_financials_handler(arguments: dict, module_name: str) -> ToolResult:
    """Handler for Balance Sheet, Cash Flow, Income Statement."""
    tickers = arguments.get("tickers")
    frequency = arguments.get("frequency", "a") # 'a' or 'q'
    
    try:
        st = SmartTicker(tickers)
        # module_name example: "balance_sheet"
        result = st.get_finance(module_name, freq=frequency)
        return ToolResult(content=[TextContent(text=f"### Bulk {module_name} ({frequency})\n\n" + result)])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_bulk_options_handler(arguments: dict) -> ToolResult:
    """Handler for Options Chain."""
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        result = st.get_options()
        return ToolResult(content=[TextContent(text=f"### Bulk Option Chain (Top 100 Rows)\n\n" + result)])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# --- SPECIFIC HANDLERS (Registered in server.py loop, but we can define custom ones here) ---

async def get_fundamental_snapshot(arguments: dict) -> ToolResult:
    """
    MULTI-TALENT: Get Price, Key Stats, and Summary Detail in one go.
    """
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        # Fetch multiple modules
        # usage: Ticker(..., modules="assetProfile summaryDetail")
        data = st.yq.get_modules("price keyStats summaryDetail financialData")
        
        if isinstance(data, dict):
            return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        elif isinstance(data, pd.DataFrame):
             return ToolResult(content=[TextContent(text=data.to_markdown())])
        return ToolResult(content=[TextContent(text=str(data))])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_ownership_report(arguments: dict) -> ToolResult:
    """MULTI-TALENT: Major Holders, Insiders, Institutions."""
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("majorHolders insiderHolders institutionOwnership fundOwnership")
        if isinstance(data, dict):
            return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        return ToolResult(content=[TextContent(text=str(data))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_earnings_report(arguments: dict) -> ToolResult:
    """MULTI-TALENT: Earnings history, trend, and calendar events."""
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("earnings earningsTrend calendarEvents")
        if isinstance(data, dict):
             return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        return ToolResult(content=[TextContent(text=str(data))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_technical_snapshot(arguments: dict) -> ToolResult:
    """MULTI-TALENT: Price, Recommendation Trend, and Index Trend."""
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("price recommendationTrend indexTrend industryTrend")
        if isinstance(data, dict):
             return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        return ToolResult(content=[TextContent(text=str(data))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
