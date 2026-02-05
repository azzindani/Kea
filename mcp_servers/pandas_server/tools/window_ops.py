import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def ewm_calc(file_path: str, span: float, agg: str, columns: List[str], output_path: str) -> str:
    """
    Exponential Weighted Moving functions.
    span: decay roughly in terms of number of observations
    agg: 'mean', 'std', 'var', 'corr'
    """
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        new_col = f"{col}_ewm_{agg}"
        
        ewm = df[col].ewm(span=span)
        if agg == 'mean':
            df[new_col] = ewm.mean()
        elif agg == 'std':
            df[new_col] = ewm.std()
        elif agg == 'var':
            df[new_col] = ewm.var()
            
    save_dataframe(df, output_path)
    return f"Calculated EWM (span={span}, agg={agg}). Saved to {output_path}"

def expanding_calc(file_path: str, agg: str, columns: List[str], output_path: str, min_periods: int = 1) -> str:
    """
    Expanding window functions (Cumulative).
    agg: 'sum', 'mean', 'max', 'min', 'std'
    """
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        new_col = f"{col}_expanding_{agg}"
        
        exp = df[col].expanding(min_periods=min_periods)
        
        if agg == 'sum': df[new_col] = exp.sum()
        elif agg == 'mean': df[new_col] = exp.mean()
        elif agg == 'max': df[new_col] = exp.max()
        elif agg == 'min': df[new_col] = exp.min()
        elif agg == 'std': df[new_col] = exp.std()
            
    save_dataframe(df, output_path)
    return f"Calculated Expanding {agg}. Saved to {output_path}"

def pct_change(file_path: str, periods: int, columns: List[str], output_path: str) -> str:
    """Calculate percentage change."""
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        new_col = f"{col}_pct_change_{periods}"
        df[new_col] = df[col].pct_change(periods=periods)
        
    save_dataframe(df, output_path)
    return f"Calculated % Change (periods={periods}). Saved to {output_path}"
