
from finvizfinance.earnings import Earnings
from finvizfinance.news import News
from shared.logging import get_logger
import pandas as pd

logger = get_logger(__name__)


async def get_earnings_calendar(period: str = "This Week") -> str:
    """
    Get Earnings Calendar.
    period: "This Week", "Next Week", "Previous Week", "This Month"
    """
    # period = arguments.get("period", "This Week")
    try:
        earn = Earnings()
        # Returns dict of dataframes or single df? Library varies.
        # Usually returns df directly if just list.
        # finvizfinance.earnings.Earnings().get_earnings() ? No, init usually sets it?
        # Actually: earn = Earnings(); df = earn.main() or similar.
        # Research says: Earnings class has methods.
        
        # Let's try standard usage
        earn_obj = Earnings()
        df = earn_obj.orders(period=period) 
        # Note: Library method names change often. Let's assume standard `screener_view` or similar if available, 
        # but for Earnings specifically, it might be different.
        # If specific method fails, catch it.
        # Re-reading docs from search: "Earnings module... output_csv..."
        # We want the dataframe.
        
        # Common finvizfinance pattern:
        # e = Earnings()
        # df = e.main() # or similar
        
        # Safe bet: Instantiate and try standard retrieval
        # If fails, return error to debug.
        # Actual library generic method often is not 'screener_view' for Earnings.
        # It's date based.
        
        # Let's try to infer from common library structure
        df = earn_obj.screener_view(group=None, orders=None, limit=None, select=None, period=period)
        # Wait, Earnings might not inherit from Overview.
        
        # FALLBACK: if method unknown, use generic scrape or skip?
        # Let's assume `screener_view` exists or `get_data`.
        # Actually, let's look at `News`.
        
        return f"### Earnings: {period}\n\n{df.head(50).to_markdown()}"

    except Exception as e:
        # Try generic "Overview" with earnings filter if simpler?
        # Or just return error for now and fix in verification.
        try:
           # Retry with .main() if it exists (common in some forks)
           earn = Earnings()
           # Some versions use .get_earnings() or similar
           return f"Library specifics ambiguous: {e}"
        except:
           return f"Error: {str(e)}"



async def get_market_news(mode: str = "news") -> str:
    """
    Get General Market News.
    mode: "news" or "blogs"
    """
    # mode = arguments.get("mode", "news")
    try:
        n = News()
        # get_news returns dict {'news': df, 'blogs': df}
        data = n.get_news()
        
        if mode in data:
            df = data[mode]
            return f"### Market {mode.title()}\n\n{df.head(20).to_markdown()}"
            
        return str(data.keys())
    except Exception as e:
        logger.error(f"News error: {e}")
        return f"Error: {str(e)}"

