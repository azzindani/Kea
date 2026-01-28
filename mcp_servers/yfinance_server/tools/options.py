
import yfinance as yf
import pandas as pd

import yfinance as yf
import pandas as pd
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_options_chain(ticker: str, date: str) -> str:
    """Get Options Chain for a specific date."""
    
    try:
        stock = yf.Ticker(ticker)
        opt = stock.option_chain(date)
        
        # Return summary to avoid exploding context
        calls = opt.calls[['contractSymbol', 'strike', 'lastPrice', 'volume', 'impliedVolatility']].head(10).to_markdown()
        puts = opt.puts[['contractSymbol', 'strike', 'lastPrice', 'volume', 'impliedVolatility']].head(10).to_markdown()
        
        return f"""
### Options Chain ({ticker} @ {date})

**Calls (Top 10)**
{calls}

**Puts (Top 10)**
{puts}
"""
    except Exception as e:
        logger.error(f"Options tool error: {e}")
        return f"Error: {str(e)}"

async def get_option_expirations(ticker: str) -> str:
    """Get available option expiration dates."""
    try:
        exps = yf.Ticker(ticker).options
        return str(exps)
    except Exception as e:
        logger.error(f"Options tool error: {e}")
        return f"Error: {str(e)}"

