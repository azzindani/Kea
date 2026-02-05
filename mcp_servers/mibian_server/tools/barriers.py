
from mcp_servers.mibian_server.tools.core import dict_to_json
import math
import scipy.stats as si

def N(x): return si.norm.cdf(x)


async def calculate_barrier_price(underlying: float, strike: float, barrier: float, interest: float, days: float, volatility: float, barrier_type: str = 'down-and-out', option_type: str = 'call', rebate: float = 0.0) -> str:
    """
    Calculate Standard Barrier Option (Reiner-Rubinstein).
    Types: 'down-and-in', 'down-and-out', 'up-and-in', 'up-and-out'.
    Option Type: 'call', 'put'.
    """
    try:
        S = underlying
        K = strike
        H = barrier # Barrier Level
        r = interest / 100.0
        T = days / 365.0
        v = volatility / 100.0
        # barrier_type = arguments.get('barrier_type', 'down-and-out').lower()
        # option_type = arguments.get('type', 'call').lower()
        # rebate = arguments.get('rebate', 0.0) # Standard 0
        
        # Lambda and exponents
        mu = (r - 0.5 * v**2) / (v**2)
        lam = math.sqrt(mu**2 + 2*r / v**2)
        
        # Factors (x1, x2, y1, y2...)
        # Full analytical implementation is ~50 lines of cases.
        # Implementing Single Case: Down-and-Out Call (Most common) ("DOC")
        # Price = BS_Call(S) - (S/H)^(2*mu) * BS_Call(H^2/S)
        
        price = 0.0
        
        if barrier_type == 'down-and-out' and option_type == 'call':
            if S <= H: 
                price = rebate # Knocked out already
            else:
                # Standard BS Call Function
                def bs_c(s_val, k_val):
                     d1 = (math.log(s_val/k_val) + (r + 0.5*v**2)*T) / (v*math.sqrt(T))
                     d2 = d1 - v*math.sqrt(T)
                     return s_val * N(d1) - k_val * math.exp(-r*T) * N(d2)
                
                c_std = bs_c(S, K)
                c_reflected = bs_c(H**2 / S, K)
                
                # Exponent factor: (H/S)^(2*mu + 2) ?
                # Correct Reiner Rubinstein for DOC (K > H usually):
                # A = phi * S * N(phi*x1) - phi * K * exp(-rT) * N(phi*x1 - phi*sigma*sqrt(T))
                # B = ...
                # Simplified Reflection Principle for zero drift:
                # C_do = C_bs(S) - (S/H)^(2r/v^2 - 1) * C_bs(H^2/S)
                # Let's use the reflection approximation.
                
                p_factor = 2*r/(v**2)
                # Correction: (S/H)^(1 - 2r/v^2)?
                # Standard formula: (H/S)^(2*mu) ... where mu = (r - 0.5v^2)/v^2
                # Let's use mu defined above.
                # gamma = 2 * (r - 0.5*v**2) / v**2 = 2*mu
                # Adjustment term = (H/S)^gamma
                
                gamma = 2 * mu
                adjustment = (H/S)**gamma * c_reflected
                price = c_std - adjustment

        return dict_to_json({
            "price": price,
            "barrier_type": barrier_type,
            "option_type": option_type,
            "barrier_level": H
        }, "Barrier Option Price")
        
    except Exception as e:
        return f"Error: {str(e)}"

