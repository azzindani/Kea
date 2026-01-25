
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_result

async def calculate_implied_volatility(arguments: dict) -> ToolResult:
    """
    Calculate IV.
    Requires CallPrice OR PutPrice.
    """
    try:
        model = arguments.get("model", "BS")
        u = arguments['underlying']
        s = arguments['strike']
        r = arguments['interest']
        d = arguments['days']
        
        args = [u, s, r, d]
        
        cp = arguments.get('call_price')
        pp = arguments.get('put_price')
        
        if cp is None and pp is None:
             raise ValueError("Must provide call_price or put_price to calc IV.")
        
        res = MibianCore.calculate(model, args, callPrice=cp, putPrice=pp)
        
        return dict_to_result({'implied_volatility': res.get('implied_volatility')}, "Implied Volatility")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
