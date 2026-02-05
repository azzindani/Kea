
from mcp_servers.finta_server.tools.core import process_ohlcv, df_to_json
from finta import TA
import pandas as pd


async def calculate_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """
    Universal Indicator Calculator for Finta.
    Args:
        data: OHLCV.
        indicator: Name (e.g. "SMA", "RSI").
        params: Dict of parameters (e.g. {"period": 14}).
    """
    try:
        indicator = indicator.upper() # Finta uses uppercase
        if params is None: params = {}
        
        df = process_ohlcv(data)
        
        if not hasattr(TA, indicator):
             return f"Indicator '{indicator}' not found in finta."
        
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
             
        return df_to_json(df, f"Indicator: {indicator}")
        
    except Exception as e:
        return f"Calculation Error: {str(e)}"

