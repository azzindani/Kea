
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
                # Only head 100000 to prevent massive overflow if not filtered
                return df.head(100000).to_markdown()
            return str(df)
        except Exception as e:
            logger.error(f"Options error: {e}")
            return f"Error: {e}"


# --- GENERIC HANDLER FOR ALL MODULES ---

async def generic_ticker_handler(tickers: str, module_name: str) -> str:
    """
    Generic handler for all Ticker attributes.
    Args:
        tickers (list[str] | str): List of symbols or space-separated string.
    """
    if not tickers:
        return "Error: No tickers provided"
    
    try:
        st = SmartTicker(tickers)
        result = st.get_module(module_name)
        
        # Add summary header
        count = len(tickers.split()) if isinstance(tickers, str) else len(tickers)
        header = f"### Bulk Data: {module_name} ({count} tickers)\n\n"
        
        return header + result
    except Exception as e:
        logger.error(f"Handler error for {module_name}: {e}")
        return f"Error: {str(e)}"



async def get_bulk_financials_handler(tickers: str, module_name: str, frequency: str = "a") -> str:
    """Handler for Balance Sheet, Cash Flow, Income Statement."""
    try:
        st = SmartTicker(tickers)
        # module_name example: "balance_sheet"
        result = st.get_finance(module_name, freq=frequency)
        return f"### Bulk {module_name} ({frequency})\n\n" + result
    except Exception as e:
        return f"Error: {str(e)}"

async def get_bulk_options_handler(tickers: str) -> str:
    """Handler for Options Chain."""
    try:
        st = SmartTicker(tickers)
        result = st.get_options()
        return f"### Bulk Option Chain (Top 100 Rows)\n\n" + result
    except Exception as e:
        return f"Error: {str(e)}"



# --- SPECIFIC HANDLERS (Registered in server.py loop, but we can define custom ones here) ---

async def get_fundamental_snapshot(tickers: str) -> str:
    """
    MULTI-TALENT: Get Price, Key Stats, and Summary Detail in one go.
    """
    try:
        st = SmartTicker(tickers)
        # Fetch multiple modules
        # usage: Ticker(..., modules="assetProfile summaryDetail")
        data = st.yq.get_modules("price keyStats summaryDetail financialData")
        
        if isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        elif isinstance(data, pd.DataFrame):
             return data.to_markdown()
        return str(data)
        
    except Exception as e:
        return f"Error: {str(e)}"

async def get_ownership_report(tickers: str) -> str:
    """MULTI-TALENT: Major Holders, Insiders, Institutions."""
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("majorHolders insiderHolders institutionOwnership fundOwnership")
        if isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        return str(data)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_earnings_report(tickers: str) -> str:
    """MULTI-TALENT: Earnings history, trend, and calendar events."""
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("earnings earningsTrend calendarEvents")
        if isinstance(data, dict):
             return json.dumps(data, indent=2, default=str)
        return str(data)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_technical_snapshot(tickers: str) -> str:
    """MULTI-TALENT: Price, Recommendation Trend, and Index Trend."""
    try:
        st = SmartTicker(tickers)
        data = st.yq.get_modules("price recommendationTrend indexTrend industryTrend")
        if isinstance(data, dict):
             return json.dumps(data, indent=2, default=str)
        return str(data)
    except Exception as e:
        return f"Error: {str(e)}"

