
from finvizfinance.quote import finvizfinance
from shared.logging import get_logger
import pandas as pd
import json

logger = get_logger(__name__)


async def get_stock_depth(ticker: str, mode: str) -> str:
    """
    Get specific depth info for a stock.
    modes: "description", "ratings", "news", "insider", "fundament"
    """
    # ticker = arguments.get("ticker")
    try:
        stock = finvizfinance(ticker)
        
        if mode == "description":
            res = stock.ticker_description()
            return res
            
        elif mode == "ratings":
            # Returns df
            df = stock.ticker_outer_ratings()
            return df.head(20).to_markdown()
            
        elif mode == "news":
            df = stock.ticker_news()
            # Columns: Date, Title, Link
            return df.head(10).to_markdown()
            
        elif mode == "insider":
            df = stock.ticker_inside_trader()
            return df.head(20).to_markdown()
            
        elif mode == "fundament":
            # Returns dict
            data = stock.ticker_fundament()
            return json.dumps(data, indent=2)
            
    except Exception as e:
        logger.error(f"Quote error {ticker} {mode}: {e}")
        return f"Error: {str(e)}"

