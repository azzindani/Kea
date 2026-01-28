
import ccxt.async_support as ccxt
import ccxt.async_support as ccxt
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)


# --- METADATA ---

async def list_exchange_markets(exchange: str = "binance") -> str:
    """
    List markets (symbols) on an exchange.
    """
    try:
        ex = await get_exchange_instance(exchange)
        symbols = ex.symbols # Loaded by load_markets()
        
        # If too many, maybe just show count and Sample?
        # Many exchanges have 1000+ pairs.
        count = len(symbols)
        sample = symbols[:50]
        
        return f"### Markets on {exchange}\nTotal: {count}\n\nSample (First 50):\n{sample}"
    except Exception as e:
        return f"Error: {str(e)}"

async def get_exchange_capabilities(exchange: str) -> str:
    """
    Check what an exchange supports (has['fetchOHLCV'], etc.).
    """
    try:
        ex = await get_exchange_instance(exchange)
        caps = {k: v for k, v in ex.has.items() if v is not False and v is not None}
        
        # Convert to DF for readability
        df = pd.DataFrame(list(caps.items()), columns=['Capability', 'Supported'])
        return f"### Capabilities: {exchange}\n\n{df.to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

