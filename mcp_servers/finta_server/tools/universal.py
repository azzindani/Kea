
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.finta_server.tools.core import process_ohlcv, df_to_result
from finta import TA
import pandas as pd

async def calculate_indicator(arguments: dict) -> ToolResult:
    """
    Universal Indicator Calculator for Finta.
    Args:
        data: OHLCV.
        indicator: Name (e.g. "SMA", "RSI").
        params: Dict of parameters (e.g. {"period": 14}). Note: Finta args are positional usually, or named.
                Wrapper will try to map params or pass as kwargs.
    """
    try:
        data = arguments.get("data")
        indicator = arguments.get("indicator").upper() # Finta uses uppercase
        params = arguments.get("params", {})
        
        df = process_ohlcv(data)
        
        if not hasattr(TA, indicator):
             return ToolResult(isError=True, content=[TextContent(text=f"Indicator '{indicator}' not found in finta.")])
        
        method = getattr(TA, indicator)
        
        # Call method
        # Finta syntax: TA.SMA(df, period=41, column='close')
        # We pass df as first arg, then **params.
        res = method(df, **params)
        
        # If Series, name it
        if hasattr(res, 'name'):
            res.name = indicator
            
        # Join to original? Usually yes.
        # But wait, universal tool might just return the result? 
        # Better to return merged DF for context.
        # Handle duplicate columns if needed.
        
        if isinstance(res, pd.Series):
             df[indicator] = res
        else:
             # DataFrame join
             res.columns = [f"{indicator}_{c}" for c in res.columns]
             df = df.join(res, how='outer')
             
        return df_to_result(df, f"Indicator: {indicator}")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=f"Calculation Error: {str(e)}")])
