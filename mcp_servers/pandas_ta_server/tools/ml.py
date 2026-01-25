
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_result
import pandas_ta as ta
import pandas as pd

async def construct_ml_dataset(arguments: dict) -> ToolResult:
    """
    Construct Machine Learning Dataset.
    Features:
    - Adds Lags (e.g. close_lag_1).
    - Adds Log Returns.
    - Adds Target (Next Day Return).
    - Drops NaNs.
    
    Args:
        data: OHLCV.
        lags: List of ints, e.g. [1, 2, 3, 5].
        features: List of indicators to add first (e.g. ["rsi", "sma_50"]). *Simplification: Assumes data already has indicators OR we run 'All'?*
                  Let's assume user calculates indicators via 'get_all_indicators' FIRST, then passes that result here?
                  Or we do it here. 
                  Efficiency: Use `df.ta.strategy` if provided.
    """
    try:
        data = arguments.get("data")
        lags = arguments.get("lags", [1, 2, 3, 5])
        target_horizon = arguments.get("target_horizon", 1) # Predict N days ahead
        
        df = process_ohlcv(data)
        
        # 1. Add Log Returns (Stationary Feature)
        df.ta.log_return(append=True)
        
        # 2. Add Lags for Close and Log Return
        cols_to_lag = ['close', 'log_return_1']
        for col in cols_to_lag:
            if col in df.columns:
                for lag in lags:
                    df[f"{col}_lag_{lag}"] = df[col].shift(lag)
                    
        # 3. Add Target (Future Return) - shifted back
        # Target = (Close[t+N] - Close[t]) / Close[t]
        # shift(-N) gives future value at current row
        df[f"target_return_{target_horizon}d"] = df['close'].shift(-target_horizon).pct_change(periods=target_horizon).shift(-1) * 100 
        # Wait, pct_change(N) calculates (Current - Previous_N) / Previous.
        # shifting(-N) brings future to now.
        # Simpler:
        future_close = df['close'].shift(-target_horizon)
        df['target'] = (future_close - df['close']) / df['close'] * 100
        
        # 4. Clean
        df.dropna(inplace=True)
        
        return df_to_result(df, "ML Dataset")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
