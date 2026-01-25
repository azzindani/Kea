
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_result
import pandas_ta as ta
import pandas as pd

async def generate_signals(arguments: dict) -> ToolResult:
    """
    Generate Signals based on a Condition.
    Args:
        data: OHLCV.
        condition: String query, e.g. "RSI_14 < 30" or "close > SMA_50".
                   Note: You must ensure the indicators exist first? 
                   NO, this tool should calculate them on the fly if implied?
                   Simplification: User provides data, we calculate ALL basic indicators, then query?
                   Better: User provides data + indicators_to_calc, then condition?
                   
                   Advanced Approach: 
                   1. Calculate "All" strategy (or specific ones needed).
                   2. Run df.query(condition).
                   
                   Efficiency: Calculating "All" is heavy but safe.
                   Let's calculate "All" for now to allow flexible querying.
    """
    try:
        data = arguments.get("data")
        condition = arguments.get("condition")
        
        df = process_ohlcv(data)
        
        # Calculate All Indicators to populate columns
        # Use verbose=False
        try:
            df.ta.strategy("All", verbose=False)
        except:
            # Manual Fallback imported from bulk? 
            # Or just duplicate logic? Importing is cleaner but circular?
            # Creating a minimal manual run here for top indicators to ensure query works.
            # actually better to import run_indicators_manually if we can moves it to core or stay in bulk?
            # circular dependency keys: bulk imports core, signals imports core. signals imports bulk? NO.
            # Logic: Let's do a mini-manual run here.
            inds = ["rsi", "sma", "ema", "bbands", "macd", "adx", "atr", "obv"]
            for ind in inds:
                try:
                   if hasattr(df.ta, ind): getattr(df.ta, ind)(append=True)
                except: pass
        
        # Filter
        try:
             # df.query expects columns to match names.
             # df columns are lower case or specific. pandas_ta names are usually UPPERCASE like 'RSI_14'.
             # core.py lowercases INPUT columns (open, close).
             # pandas_ta OUTPUT columns are usually upper case (RSI_14).
             
             # Let's let the user guess or provide help.
             signals = df.query(condition)
             
             return df_to_result(signals, "Signals")
        except Exception as e:
             return ToolResult(isError=True, content=[TextContent(text=f"Query Error: {str(e)}. Available Cols: {list(df.columns)}")])
             
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def calculate_tsignals(arguments: dict) -> ToolResult:
    """
    Calculate Algorithmic Trend Signals.
    Wraps separate Trend Indicator + tsignals?
    Actually tsignals needs 'trend' input column.
    Simplification: Can we run it on Price? No.
    It processes a Trend Series.
    Maybe skip for now as it requires complex chaining (User calculate trend -> User passes trend -> calculate_tsignals).
    Let's rely on 'generate_signals' which is more robust for LLM logic.
    Instead, let's implement 'calculate_chop' (Choppiness Index) - valuable for filtering trends.
    """
    # Chop Index is simpler and standalone.
    # arguments['indicator'] = 'chop'
    # return await calculate_indicator(arguments)
    # Moving tsignals idea to 'Choppiness Index' which is more useful "out of the box".
    from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator
    arguments['indicator'] = 'chop'
    return await calculate_indicator(arguments)
