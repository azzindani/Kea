
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_result

async def calculate_bs_price(arguments: dict) -> ToolResult:
    """
    Calculate Black-Scholes Option Price (Call & Put).
    Args:
        underlying, strike, interest, days, volatility.
    """
    try:
        u = arguments['underlying']
        s = arguments['strike']
        r = arguments['interest']
        d = arguments['days']
        v = arguments['volatility']
        
        args = [u, s, r, d]
        res = MibianCore.calculate("BS", args, volatility=v)
        
        # Filter for just price? User usually wants everything.
        # But if specifically asking for price, let's ensure it's there.
        return dict_to_result(res, "BS Price")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def calculate_gk_price(arguments: dict) -> ToolResult:
    """Garman-Kohlhagen (Currencies) Price."""
    try:
        args = [arguments['underlying'], arguments['strike'], arguments['interest'], arguments['days']]
        res = MibianCore.calculate("GK", args, volatility=arguments['volatility'])
        return dict_to_result(res, "GK Price")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def calculate_me_price(arguments: dict) -> ToolResult:
    """Merton (Dividends) Price."""
    try:
        args = [arguments['underlying'], arguments['strike'], arguments['interest'], arguments['days']]
        res = MibianCore.calculate("Me", args, volatility=arguments['volatility'])
        return dict_to_result(res, "Merton Price")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
