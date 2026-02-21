
import asyncio
import yfinance as yf
import pandas as pd
from mcp_servers.yfinance_server.utils.ticker_cache import TickerCache
from shared.logging.main import get_logger

logger = get_logger(__name__)

cache = TickerCache()

async def get_tickers_by_country(country_code: str, limit: int = 50) -> str:
    """
    Get all stock tickers for a specific country or exchange.
    
    Use this tool to find "all companies" or "tickers" for a region.
    Supported inputs: "US" (USA), "ID" (Indonesia/IDX), "IN" (India), etc.
    Returns size of universe and sample tickers.
    
    Args:
        country_code: ISO 2 character country code (e.g. "US")
        limit: Number of tickers to sample for the report (default: 50)
    """
    
    try:
        # Ensure it's awaited and robust against potential issues
        tickers_coro = cache.get_tickers_for_country(country_code)
        if asyncio.iscoroutine(tickers_coro):
            tickers = await tickers_coro
        else:
            tickers = tickers_coro
            
        if not tickers:
            return f"No ticker list found for country: {country_code}"
        
        # Download snapshot (1d price)
        # Use limit to avoid massive downloads in discovery
        sample_tickers = tickers[:limit]
        df = yf.download(sample_tickers, period="1d", group_by="ticker", threads=True, progress=False)
        
        if df.empty:
            return f"Scanned {len(tickers)} tickers for {country_code}, but no market data was available for samples."

        # Extract last Close for summary
        if isinstance(df.columns, pd.MultiIndex):
            closes = {t: df[t]['Close'].iloc[-1] for t in sample_tickers if t in df.columns.levels[0]}
        else:
            closes = df['Close'].to_dict()
        
        # Just return summary stats
        return f"""
### Country Scan: {country_code}
Scanned {len(tickers)} tickers.

Sample Data (Top 5):
{str(list(closes.items())[:5])}

(Full data available seamlessly via 'get_bulk_historical_data' if needed)
"""
        
    except Exception as e:
        logger.error(f"Discovery tool error: {e}", exc_info=True)
        return f"Error: {str(e)}"

