
from yahooquery import get_trending
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
import json

logger = get_logger(__name__)


async def get_market_trending(country: str = "united states", count: int = 10) -> str:
    """
    Get trending securities for a specific region.
    Args:
        country (str): "US", "ID", "AU", "GB", etc. (Default: US)
        count (int): (Optional) Limit results (default 10)
    """
    
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
    
    country_lower = country.lower()
    if country_lower in MAPPING:
        country_code = MAPPING[country_lower]
    else:
        country_code = country
        
    try:
        # yahooquery.get_trending returns a dict
        data = get_trending(country_code)
        
        if "quotes" in data:
            # Simplify
            quotes = data["quotes"][:count]
            return json.dumps(quotes, indent=2)
            
        return json.dumps(data, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Trending error for {country}: {e}")
        return f"Error: {str(e)}"

