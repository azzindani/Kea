
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_transaction_history(arguments: dict) -> ToolResult:
    """
    Get Transaction History (Ledger/Deposits/Withdrawals).
    """
    exchange_id = arguments.get("exchange", "binance")
    code = arguments.get("code") # Currency code e.g. "USDT", optional
    limit = arguments.get("limit", 20)
    
    try:
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
             
        if exchange.has['fetchLedger']:
            ledger = await exchange.fetch_ledger(code, limit=limit)
            df = pd.DataFrame(ledger)
            # keys: id, timestamp, datetime, currency, amount, type (deposit/withdraw/trade/fee), status
            cols = ['id', 'datetime', 'currency', 'amount', 'type', 'status', 'fee']
            cols = [c for c in cols if c in df.columns]
            return ToolResult(content=[TextContent(text=f"### Ledger: {exchange_id}\n\n{df[cols].to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchLedger.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_deposit_address(arguments: dict) -> ToolResult:
    """
    Get Deposit Address for a Currency.
    """
    exchange_id = arguments.get("exchange", "binance")
    code = arguments.get("code", "BTC")
    
    try:
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])

        if exchange.has['fetchDepositAddress']:
            address = await exchange.fetch_deposit_address(code)
            # keys: currency, address, tag, network
            return ToolResult(content=[TextContent(text=f"### Deposit Address: {code} on {exchange_id}\nAddress: `{address.get('address')}`\nTag: `{address.get('tag')}`\nNetwork: {address.get('network')}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchDepositAddress.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
