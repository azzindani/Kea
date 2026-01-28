
from mcp_servers.mibian_server.tools.core import MibianCore, df_to_json
import pandas as pd
import numpy as np


async def simulate_greek_scenario(underlying_start: float, underlying_end: float, steps: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """
    Simulate Option behavior across a price range.
    Args:
        - underlying_start, underlying_end, steps
        - strike, interest, days, volatility
    Returns: DataFrame of Price/Delta/Gamma/Theta at each price step.
    """
    try:
        start = underlying_start
        end = underlying_end
        steps = int(steps) # arguments.get('steps', 20)
        
        s = strike
        r = interest
        d = days
        v = volatility
        
        prices = np.linspace(start, end, steps)
        results = []
        
        for u in prices:
            # Calc BS
            args = [u, s, r, d]
            res = MibianCore.calculate("BS", args, volatility=v)
            res['scenario_underlying'] = u
            results.append(res)
            
        df = pd.DataFrame(results)
        return df_to_json(df, "Scenario Simulation")
    except Exception as e:
        return f"Error: {str(e)}"

