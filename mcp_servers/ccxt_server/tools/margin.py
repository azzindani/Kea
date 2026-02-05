
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_borrow_rates(arguments: dict) -> ToolResult:
    """
    Get Borrow Rates (Margin).
    """
    exchange_id = arguments.get("exchange", "binance")
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if exchange.has['fetchBorrowRates']:
            rates = await exchange.fetch_borrow_rates()
            # Returns dict { currency: { ... } }
            # Convert to list
            data = []
            for cur, info in rates.items():
                # Info structure varies, usually 'rate', 'timestamp'
                info['currency'] = cur
                data.append(info)
            
            df = pd.DataFrame(data)
            return ToolResult(content=[TextContent(text=f"### Borrow Rates: {exchange_id}\n\n{df.head(20).to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchBorrowRates.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_leverage_tiers(arguments: dict) -> ToolResult:
    """
    Get Leverage Tiers (Max Leverage & Maintenance Margin).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbols = arguments.get("symbols") # List or none
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if exchange.has['fetchLeverageTiers']:
            tiers = await exchange.fetch_leverage_tiers(symbols)
            # Returns dict { symbol: [tiers...] }
            # If large number of symbols (None), this is huge.
            # Just show sample for first symbol if not specified
            
            output = ""
            count = 0
            for sym, tier_list in tiers.items():
                df = pd.DataFrame(tier_list)
                output += f"#### {sym}\n{df.to_markdown()}\n\n"
                count += 1
                if count >= 3:
                    output += "\n...(Truncated for brevity)..."
                    break
            
            return ToolResult(content=[TextContent(text=f"### Leverage Tiers: {exchange_id}\n\n{output}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchLeverageTiers.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
