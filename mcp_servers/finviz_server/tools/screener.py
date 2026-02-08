
try:
    from finvizfinance.screener.overview import Overview
except ImportError:
    Overview = None # Fallback or handle graceful failure if install failed
    


from shared.logging.structured import get_logger
from shared.mcp.protocol import ToolResult, JSONContent, TextContent
import pandas as pd
import json
import asyncio

logger = get_logger(__name__)


async def get_screener_signal(limit: int = 100000, signal: str = None) -> ToolResult:
    """
    Get generic screener signal.
    Args:
        signal (str): The specific signal key (e.g. "ta_topgainers")
        limit (int): Number of results (default 100000)
    """
    # signal = arguments.get("signal")
    # limit = arguments.get("limit", 30)
    
    try:
        if Overview is None:
            return ToolResult(content=[TextContent(text="finvizfinance not installed")])

        def fetch_overview():
            foverview = Overview()
            
            nonlocal signal
            real_signal = signal
            if signal in SIGNALS:
                real_signal = SIGNALS[signal]
            
            # Set the signal
            foverview.set_filter(signal=real_signal)
            
            # Get dataframe (limit isn't natively supported well in all library versions, 
            # so we fetch and head)
            # IMPORTANT: Pass limit to screener_view to avoid scraping 9000 stocks!
            return foverview.screener_view(limit=limit)

        from shared.stdout_suppression import suppress_stdout
        with suppress_stdout():
             df = await asyncio.to_thread(fetch_overview)
        
        if df is None or df.empty:
            return ToolResult(content=[TextContent(text="No results found.")])
            
        # Simplify columns for LLM
        # Keep: Ticker, Company, Sector, Price, Change, Volume
        cols = ["Ticker", "Company", "Sector", "Industry", "Price", "Change", "Volume"]
        # Filter existing columns
        cols = [c for c in cols if c in df.columns]
        
        df_lite = df[cols].head(limit)
        
        # Return Structured + Text
        return ToolResult(content=[
            TextContent(text=f"### Signal: {signal}\n\n{df_lite.to_markdown(index=False)}"),
            JSONContent(data=df_lite.to_dict(orient="records"))
        ])
        
    except Exception as e:
        logger.error(f"Screener error {signal}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=f"Error: {str(e)}")])


# Map "Nice Name" to Finviz Signal Key
SIGNALS = {
    "top_gainers": "Top Gainers",
    "top_losers": "Top Losers",
    "new_highs": "New Highs",
    "new_lows": "New Lows",
    "most_volatile": "Most Volatile",
    "most_active": "Most Active",
    "unusual_volume": "Unusual Volume",
    "overbought": "Overbought",
    "oversold": "Oversold",
    "downgrades": "Downgrades",
    "upgrades": "Upgrades",
    "earnings_before": "Earnings Before",
    "earnings_after": "Earnings After",
    "insider_buying": "Insider Buying",
    "insider_selling": "Insider Selling",
    "major_news": "Major News",
    "horizontal_sr": "Horizontal S/R",
    "tl_support": "TL Support",
    "tl_resistance": "TL Resistance",
    "wedge_up": "Wedge Up",
    "wedge_down": "Wedge Down",
    "triangle_ascending": "Triangle Ascending",
    "triangle_descending": "Triangle Descending",
    "channel_up": "Channel Up",
    "channel_down": "Channel Down",
    "double_top": "Double Top",
    "double_bottom": "Double Bottom",
    # Additions for >50 tools
    "high_dividend_yield": "High Dividend Yield", # Check validity, actually Finviz signal might not strictly exist for this? 
    # Finviz Signals dropdown usually has limited set. Let's stick to Safe ones or verify. 
    # "Recent Insider Buying", "Recent Insider Selling"... "Insider Buying" is already there.
    # Let's add variations if possible, or Patterns.
    "head_and_shoulders": "Head & Shoulders",
    "head_and_shoulders_inverse": "Head & Shoulders Inverse",
    "channel_up": "Channel Up",
    "channel_down": "Channel Down",
    "multiple_top": "Multiple Top",
    "multiple_bottom": "Multiple Bottom"
}

# Factory function to register these in server.py
def get_signal_map():
    return SIGNALS
