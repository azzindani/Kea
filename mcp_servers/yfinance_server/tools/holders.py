import yfinance as yf
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_major_holders_breakdown(ticker: str, **kwargs) -> str:
    """Get breakdown of insiders vs institutions."""
    try:
        df = yf.Ticker(ticker).major_holders
        return df.to_markdown() if df is not None else "N/A"
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return f"Error: {str(e)}"

async def get_institutional_holders(ticker: str, **kwargs) -> str:
    """Get top institutional holders."""
    try:
        df = yf.Ticker(ticker).institutional_holders
        return df.to_markdown() if df is not None else "N/A"
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return f"Error: {str(e)}"

async def get_mutual_fund_holders(ticker: str, **kwargs) -> str:
    """Get top mutual fund holders."""
    try:
        df = yf.Ticker(ticker).mutualfund_holders
        return df.to_markdown() if df is not None else "N/A"
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return f"Error: {str(e)}"

async def get_insider_transactions(ticker: str, limit: int = 1000, **kwargs) -> str:
    """Get recent insider transactions."""
    try:
        df = yf.Ticker(ticker).insider_transactions
        return df.head(limit).to_markdown() if df is not None else "N/A"
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return f"Error: {str(e)}"

async def get_insider_roster(ticker: str, **kwargs) -> str:
    """Get insider roster."""
    try:
        df = yf.Ticker(ticker).insider_roster_holders
        return df.to_markdown() if df is not None else "N/A"
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return f"Error: {str(e)}"

