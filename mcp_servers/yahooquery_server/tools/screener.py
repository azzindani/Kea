
from yahooquery import Screener
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import json

logger = get_logger(__name__)

async def get_screen_data(arguments: dict) -> ToolResult:
    """
    Get data from a specific predefined screener list.
    Args:
        preset (str): "day_gainers", "day_losers", "most_actives", "cryptocurrencies"
        count (int): Number of results (default 25)
    """
    preset = arguments.get("preset", "day_gainers")
    count = arguments.get("count", 25)
    
    try:
        s = Screener()
        data = s.get_screeners(preset, count=count)
        
        # Data is a dict where keys are the preset names
        # e.g. {'day_gainers': {...}}
        if preset in data:
            real_data = data[preset]
            if "quotes" in real_data:
                # Simplify output for LLM
                quotes = real_data["quotes"]
                # Keep only key fields
                simple = [{k: q.get(k) for k in ["symbol", "shortName", "regularMarketPrice", "regularMarketChangePercent", "marketCap"]} for q in quotes]
                return ToolResult(content=[TextContent(text=json.dumps(simple, indent=2))])
                
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        
    except Exception as e:
        logger.error(f"Screener error for {preset}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
