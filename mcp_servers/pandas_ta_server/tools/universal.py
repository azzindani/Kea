
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_json
import pandas_ta as ta


async def calculate_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """
    Universal Indicator Calculator.
    Args:
        data: OHLCV Data.
        indicator: Name (e.g. "rsi", "bbands").
        params: Dictionary of parameters (e.g. {"length": 14}).
    """
    try:
        indicator = indicator.lower()
        if params is None: params = {}
        
        df = process_ohlcv(data)
        
        # Dynamic Call: df.ta.indicator_name(append=True, **params)
        # We use the ta extension
        if not hasattr(df.ta, indicator):
             return f"Indicator '{indicator}' not found in pandas_ta."
        
        method = getattr(df.ta, indicator)
        
        method(append=True, **params)
        
        # Return the whole DF with appended columns
        return df_to_json(df, f"Indicator: {indicator}")
        
    except Exception as e:
        return f"Calculation Error: {str(e)}"

