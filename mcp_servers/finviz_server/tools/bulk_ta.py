
from finvizfinance.screener.technical import Technical

from shared.logging import get_logger

logger = get_logger(__name__)


async def get_technical_table(limit: int = 100000, signal: str = "") -> str:
    """
    Get Bulk Technical Analysis Table (RSI, SMA, ATR, Volatility).
    """
    # signal = arguments.get("signal", "") # Optional signal to filter by
    # limit = arguments.get("limit", 50)
    
    try:
        tech = Technical()
        if signal:
            tech.set_filter(signal=signal)
            
        # screener_view defaults to Technical columns [Ticker, ..., RSI, SMA20, SMA50, SMA200, 52W High, ...]
        df = tech.screener_view()
        
        return f"### Bulk Technicals (Top {limit})\n\n{df.head(limit).to_markdown(index=False)}"
        
    except Exception as e:
        return f"Error: {str(e)}"

