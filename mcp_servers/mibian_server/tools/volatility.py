
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_json


async def calculate_implied_volatility(underlying: float, strike: float, interest: float, days: float, call_price: float = None, put_price: float = None, model: str = "BS") -> str:
    """CALCULATES IV. [ACTION]
    
    [RAG Context]
    Calculate Implied Volatility.
    Requires CallPrice OR PutPrice.
    Returns JSON string.
    """
    try:
        # model = arguments.get("model", "BS")
        # u = arguments['underlying']
        # s = arguments['strike']
        # r = arguments['interest']
        # d = arguments['days']
        
        args = [underlying, strike, interest, days]
        
        # cp = arguments.get('call_price')
        # pp = arguments.get('put_price')
        
        if call_price is None and put_price is None:
             raise ValueError("Must provide call_price or put_price to calc IV.")
        
        res = MibianCore.calculate(model, args, callPrice=call_price, putPrice=put_price)
        
        return dict_to_json({'implied_volatility': res.get('implied_volatility')}, "Implied Volatility")
    except Exception as e:
        return f"Error: {str(e)}"

