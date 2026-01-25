
from finvizfinance.forex import Forex
from finvizfinance.crypto import Crypto
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_global_performance(arguments: dict, asset_class: str) -> ToolResult:
    """
    Get generic performance table for Forex or Crypto.
    asset_class: "forex" or "crypto"
    """
    try:
        if asset_class == "forex":
            obj = Forex()
            # method is usually .performance() returning df
            df = obj.performance()
        elif asset_class == "crypto":
            obj = Crypto()
            df = obj.performance()
        else:
            return ToolResult(isError=True, content=[TextContent(text="Invalid asset class")])
            
        return ToolResult(content=[TextContent(text=f"### Global: {asset_class.title()} Performance\n\n{df.to_markdown()}")])
        
    except Exception as e:
        logger.error(f"Global error {asset_class}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
