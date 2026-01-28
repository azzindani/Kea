
from mcp_servers.mibian_server.tools.core import dict_to_json
import math
import scipy.stats as si


async def calculate_binary_price(underlying: float, strike: float, interest: float, days: float, volatility: float, payout: float = 100.0) -> str:
    """
    Calculate Binary Initial (Cash-or-Nothing) Option Price.
    Mibian doesn't support this natively, implemented manually.
    Price = e^(-rT) * N(d2). (For Call).
    """
    try:
        u = underlying # arguments['underlying']
        s = strike # arguments['strike']
        r = interest / 100.0
        d = days / 365.0
        v = volatility / 100.0
        # payout = arguments.get('payout', 100.0) # Cash payout amount
        
        if d <= 0: return dict_to_json({"price": payout if u>s else 0}, "Binary Result")
        
        num = math.log(u/s) + (r - 0.5 * v**2) * d
        den = v * math.sqrt(d)
        d2 = num / den
        
        nd2 = si.norm.cdf(d2)
        nd2_neg = si.norm.cdf(-d2)
        
        # Cash-or-Nothing Call
        call_price = math.exp(-r * d) * nd2 * payout
        
        # Cash-or-Nothing Put
        put_price = math.exp(-r * d) * nd2_neg * payout
        
        return dict_to_json({
            "binary_call_price": call_price,
            "binary_put_price": put_price,
            "payout_amount": payout
        }, "Binary Option Price")
        
    except Exception as e:
        return f"Error: {str(e)}"

