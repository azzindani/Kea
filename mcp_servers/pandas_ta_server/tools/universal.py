
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_result
import pandas_ta as ta

async def calculate_indicator(arguments: dict) -> ToolResult:
    """
    Universal Indicator Calculator.
    Args:
        data: OHLCV Data.
        indicator: Name (e.g. "rsi", "bbands").
        params: Dictionary of parameters (e.g. {"length": 14}).
    """
    try:
        data = arguments.get("data")
        indicator = arguments.get("indicator").lower()
        params = arguments.get("params", {})
        
        df = process_ohlcv(data)
        
        # Dynamic Call: df.ta.indicator_name(append=True, **params)
        # We use the ta extension
        if not hasattr(df.ta, indicator):
             return ToolResult(isError=True, content=[TextContent(text=f"Indicator '{indicator}' not found in pandas_ta.")])
        
        method = getattr(df.ta, indicator)
        
        # Call method
        # some indicators return a DF, some a Series. append=True ensures it's added to df.
        # But here maybe we just want the result?
        # If we append=True, we manipulate df and return it.
        # Let's use append=True to handle Multi-Column outputs (like BBands -> Lower, Mid, Upper) automatically.
        
        # Clean params (convert strings to numbers if needed?)
        # For now assume JSON handles types correctly.
        
        method(append=True, **params)
        
        # Return the whole DF with appended columns
        return df_to_result(df, f"Indicator: {indicator}")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=f"Calculation Error: {str(e)}")])
