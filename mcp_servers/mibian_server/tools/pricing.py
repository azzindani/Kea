
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_json


async def calculate_bs_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Price. [ACTION]
    
    [RAG Context]
    Black-Scholes Option Price (Call & Put).
    Returns JSON string.
    """
    try:
        # u = arguments['underlying']
        # s = arguments['strike']
        # r = arguments['interest']
        # d = arguments['days']
        # v = arguments['volatility']
        
        args = [underlying, strike, interest, days]
        res = MibianCore.calculate("BS", args, volatility=volatility)
        
        # Filter for just price? User usually wants everything.
        # But if specifically asking for price, let's ensure it's there.
        return dict_to_json(res, "BS Price")
    except Exception as e:
        return f"Error: {str(e)}"

async def calculate_gk_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES GK Price. [ACTION]
    
    [RAG Context]
    Garman-Kohlhagen (Currencies) Option Price.
    Returns JSON string.
    """
    try:
        args = [underlying, strike, interest, days]
        res = MibianCore.calculate("GK", args, volatility=volatility)
        return dict_to_json(res, "GK Price")
    except Exception as e:
        return f"Error: {str(e)}"

async def calculate_me_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Merton Price. [ACTION]
    
    [RAG Context]
    Merton (Dividends) Option Price.
    Returns JSON string.
    """
    try:
        args = [underlying, strike, interest, days]
        res = MibianCore.calculate("Me", args, volatility=volatility)
        return dict_to_json(res, "Merton Price")
    except Exception as e:
        return f"Error: {str(e)}"

