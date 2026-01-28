
from finvizfinance.quote import finvizfinance

from shared.logging import get_logger

logger = get_logger(__name__)


async def get_chart_url(ticker: str, timeframe: str = "daily", type: str = "candle") -> str:
    """
    Get Finviz Chart Image URL.
    timeframe: "daily" (d), "weekly" (w), "monthly" (m)
    type: "candle", "line"
    """
    # ticker = arguments.get("ticker")
    # timeframe = arguments.get("timeframe", "daily")
    # chart_type = arguments.get("type", "candle")
    chart_type = type # Rename to avoid conflict with 'type' builtin (though ok in signature)
    
    try:
        # Map nice names to finviz codes if needed
        # Actually, finvizfinance ticker_charts takes arguments but doesn't return URL easily?
        # Let's construct standard URL pattern if library is difficult, 
        # OR use the library if it exposes it.
        # Research says: stock.ticker_charts returns nothing, it downloads?
        
        # Standard Finviz Chart URLs are predictable:
        # https://finviz.com/chart.ashx?t=AAPL&ty=c&ta=1&p=d&s=l
        # t=Ticker, ty=Type (c=candle), ta=1 (advanced?), p=Period (d,w,m)
        
        tf_map = {"daily": "d", "weekly": "w", "monthly": "m", "intraday": "i"}
        ty_map = {"candle": "c", "line": "l"}
        
        tf_code = tf_map.get(timeframe, "d")
        ty_code = ty_map.get(chart_type, "c")
        
        url = f"https://finviz.com/chart.ashx?t={ticker}&ty={ty_code}&ta=1&p={tf_code}&s=l"
        
        return url
        
    except Exception as e:
        return f"Error: {str(e)}"

