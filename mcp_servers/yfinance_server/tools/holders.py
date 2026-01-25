
import yfinance as yf
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_major_holders_breakdown(arguments: dict) -> ToolResult:
    """Get breakdown of insiders vs institutions."""
    try:
        df = yf.Ticker(arguments.get("ticker")).major_holders
        return ToolResult(content=[TextContent(text=df.to_markdown())])
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_institutional_holders(arguments: dict) -> ToolResult:
    """Get top institutional holders."""
    try:
        df = yf.Ticker(arguments.get("ticker")).institutional_holders
        return ToolResult(content=[TextContent(text=df.to_markdown())])
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_mutual_fund_holders(arguments: dict) -> ToolResult:
    """Get top mutual fund holders."""
    try:
        df = yf.Ticker(arguments.get("ticker")).mutualfund_holders
        return ToolResult(content=[TextContent(text=df.to_markdown())])
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_insider_transactions(arguments: dict) -> ToolResult:
    """Get recent insider transactions."""
    try:
        df = yf.Ticker(arguments.get("ticker")).insider_transactions
        return ToolResult(content=[TextContent(text=df.head(20).to_markdown())])
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_insider_roster(arguments: dict) -> ToolResult:
    """Get insider roster."""
    try:
        df = yf.Ticker(arguments.get("ticker")).insider_roster_holders
        return ToolResult(content=[TextContent(text=df.to_markdown())])
    except Exception as e: 
        logger.error(f"Holders tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
