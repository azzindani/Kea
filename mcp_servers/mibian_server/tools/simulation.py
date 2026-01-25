
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.mibian_server.tools.core import MibianCore, df_to_result
import pandas as pd
import numpy as np

async def simulate_greek_scenario(arguments: dict) -> ToolResult:
    """
    Simulate Option behavior across a price range.
    Args:
        - underlying_start, underlying_end, steps
        - strike, interest, days, volatility
    Returns: DataFrame of Price/Delta/Gamma/Theta at each price step.
    """
    try:
        start = arguments['underlying_start']
        end = arguments['underlying_end']
        steps = arguments.get('steps', 20)
        
        s = arguments['strike']
        r = arguments['interest']
        d = arguments['days']
        v = arguments['volatility']
        
        prices = np.linspace(start, end, steps)
        results = []
        
        for u in prices:
            # Calc BS
            args = [u, s, r, d]
            res = MibianCore.calculate("BS", args, volatility=v)
            res['scenario_underlying'] = u
            results.append(res)
            
        df = pd.DataFrame(results)
        return df_to_result(df, "Scenario Simulation")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
