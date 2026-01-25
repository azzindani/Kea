
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def list_exchange_markets(arguments: dict) -> ToolResult:
    """
    List markets (symbols) on an exchange.
    """
    exchange_id = arguments.get("exchange", "binance")
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        symbols = exchange.symbols # Loaded by load_markets()
        
        # If too many, maybe just show count and Sample?
        # Many exchanges have 1000+ pairs.
        count = len(symbols)
        sample = symbols[:50]
        
        return ToolResult(content=[TextContent(text=f"### Markets on {exchange_id}\nTotal: {count}\n\nSample (First 50):\n{sample}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_exchange_capabilities(arguments: dict) -> ToolResult:
    """
    Check what an exchange supports (has['fetchOHLCV'], etc.).
    """
    exchange_id = arguments.get("exchange")
    try:
        exchange = await get_exchange_instance(exchange_id)
        caps = {k: v for k, v in exchange.has.items() if v is not False and v is not None}
        
        # Convert to DF for readability
        df = pd.DataFrame(list(caps.items()), columns=['Capability', 'Supported'])
        return ToolResult(content=[TextContent(text=f"### Capabilities: {exchange_id}\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
