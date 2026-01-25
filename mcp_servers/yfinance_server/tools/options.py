
import yfinance as yf
import pandas as pd
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_options_chain(arguments: dict) -> ToolResult:
    """Get Options Chain for a specific date."""
    ticker = arguments.get("ticker")
    date = arguments.get("date") # YYYY-MM-DD
    
    try:
        stock = yf.Ticker(ticker)
        opt = stock.option_chain(date)
        
        # Return summary to avoid exploding context
        calls = opt.calls[['contractSymbol', 'strike', 'lastPrice', 'volume', 'impliedVolatility']].head(10).to_markdown()
        puts = opt.puts[['contractSymbol', 'strike', 'lastPrice', 'volume', 'impliedVolatility']].head(10).to_markdown()
        
        return ToolResult(content=[TextContent(text=f"""
### Options Chain ({ticker} @ {date})

**Calls (Top 10)**
{calls}

**Puts (Top 10)**
{puts}
""")])
    except Exception as e:
        logger.error(f"Options tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_option_expirations(arguments: dict) -> ToolResult:
    """Get available option expiration dates."""
    ticker = arguments.get("ticker")
    try:
        exps = yf.Ticker(ticker).options
        return ToolResult(content=[TextContent(text=str(exps))])
    except Exception as e:
        logger.error(f"Options tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
