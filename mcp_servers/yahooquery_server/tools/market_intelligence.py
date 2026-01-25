
from yahooquery import get_trending
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import json

logger = get_logger(__name__)

async def get_market_trending(arguments: dict) -> ToolResult:
    """
    Get trending securities for a specific region.
    Args:
        country (str): "US", "ID", "AU", "GB", etc. (Default: US)
        count (int): (Optional) Limit results (default 10)
    """
    country = arguments.get("country", "united states").lower()
    count = arguments.get("count", 10)
    
    # Map common codes to full names if needed by yahooquery trending
    MAPPING = {
        "us": "united states",
        "usa": "united states",
        "id": "indonesia",
        "au": "australia",
        "gb": "united kingdom",
        "uk": "united kingdom",
        "cn": "china",
        "jp": "japan",
        "de": "germany",
    }
    
    if country in MAPPING:
        country = MAPPING[country]
        
    try:
        # yahooquery.get_trending returns a dict
        data = get_trending(country)
        
        if "quotes" in data:
            # Simplify
            quotes = data["quotes"][:count]
            return ToolResult(content=[TextContent(text=json.dumps(quotes, indent=2))])
            
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
        
    except Exception as e:
        logger.error(f"Trending error for {country}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
