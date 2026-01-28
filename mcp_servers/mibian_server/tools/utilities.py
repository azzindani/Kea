
from mcp_servers.mibian_server.tools.core import MibianCore, dict_to_json
import math


async def calculate_put_call_parity(call_price: float, put_price: float, underlying: float, strike: float, interest: float, days: float) -> str:
    """
    Check Put-Call Parity.
    Inputs: call_price, put_price, underlying, strike, interest, days.
    Output: Arbitrage Amount (Difference).
    """
    try:
        c = call_price # arguments['call_price']
        p = put_price # arguments['put_price']
        u = underlying # arguments['underlying']
        s = strike # arguments['strike']
        r = interest / 100.0 # Standardize to decimal? Mibian takes 0-100 usually?
        # Mibian takes interest as number, e.g. 5 for 5%.
        # Let's check Mibian convention. Mibian takes rate as percentage (e.g. 1.5).
        # We should assume user provides standard Mibian format.
        
        # Parity: C + PV(K) = P + S
        # PV(K) = K * e^(-r*T)
        t = days / 365.0
        
        # Convert Rate: Mibian uses Annual %, so we divide by 100 for Math.
        rate_decimal = interest / 100.0
        
        # PV(K)
        pv_strike = s * math.exp(-rate_decimal * t)
        
        lhs = c + pv_strike
        rhs = p + u
        diff = lhs - rhs
        
        return dict_to_json({
            "call_plus_bond": lhs,
            "put_plus_stock": rhs,
            "parity_difference": diff,
            "arbitrage_opportunity": abs(diff) > 0.1 # Arbitrary threshold
        }, "Put-Call Parity")
    except Exception as e:
        return f"Error: {str(e)}"



async def calculate_moneyness(underlying: float, strike: float) -> str:
    """Calculate Moneyness (% ITM/OTM)."""
    try:
        u = underlying # arguments['underlying']
        s = strike # arguments['strike']
        
        # Simply U/K
        moneyness = u / s
        ln_moneyness = math.log(u / s)
        
        return dict_to_json({
            "moneyness_ratio": moneyness,
            "log_moneyness": ln_moneyness,
            "itm_call": u > s,
            "itm_put": s > u
        }, "Moneyness")
    except Exception as e:
        return f"Error: {str(e)}"



async def calculate_probability_itm(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """
    Estimate Probability of Expiring ITM (Dual Delta).
    Uses N(d2). mibian calculates Delta (N(d1)). 
    We might need to roughly estimate or re-implement d2 logic.
    Actually, delta is often used as rough approximation (N(d1)).
    But true probability is N(d2).
    
    Since Mibian doesn't expose d2 directly, we can compute it.
    d2 = d1 - vol * sqrt(T)
    """
    try:
        # We can implement d2 calculation manually.
        u = underlying # arguments['underlying']
        s = strike # arguments['strike']
        r = interest / 100.0
        d = days / 365.0
        v = volatility / 100.0
        
        import scipy.stats as si
        # d1 = (ln(S/K) + (r + 0.5 v^2)T) / (v sqrt(T))
        # d2 = d1 - v sqrt(T)
        
        if d <= 0: return dict_to_json({"prob_itm": 0 if u < s else 1}, "Probability ITM")
        
        num = math.log(u/s) + (r + 0.5 * v**2) * d
        den = v * math.sqrt(d)
        d1 = num / den
        d2 = d1 - v * math.sqrt(d)
        
        nd2 = si.norm.cdf(d2)
        
        return dict_to_json({
            "prob_itm_call": nd2,
            "prob_itm_put": 1 - nd2, # N(-d2)
            "d1": d1,
            "d2": d2
        }, "Probability ITM")
    except Exception as e:
         return f"Error: {str(e)}"



async def calculate_dual_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    # Alias for Prob ITM
    return await calculate_probability_itm(underlying, strike, interest, days, volatility)

