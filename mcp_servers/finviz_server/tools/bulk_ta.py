
import asyncio
from finvizfinance.screener.technical import Technical

from shared.logging.main import get_logger

logger = get_logger(__name__)


async def get_technical_table(limit: int = 100000, signal: str = "") -> str:
    """
    Get Bulk Technical Analysis Table (RSI, SMA, ATR, Volatility).
    """
    # signal = arguments.get("signal", "") # Optional signal to filter by
    # limit = arguments.get("limit", 50)
    
    try:
        def fetch_tech():
            tech = Technical()
            if signal:
                tech.set_filter(signal=signal)
            # Use limit to avoid scraping everything if possible
            # finvizfinance supports limit but sometimes retrieves more if filters are loose.
            # Passing limit=limit ensures we don't fetch 9000 pages.
            return tech.screener_view(limit=limit)

        # Run blocking call in thread
        df = await asyncio.to_thread(fetch_tech)
        
        return f"### Bulk Technicals (Top {limit})\n\n{df.head(limit).to_markdown(index=False)}"
        
    except Exception as e:
        return f"Error: {str(e)}"

