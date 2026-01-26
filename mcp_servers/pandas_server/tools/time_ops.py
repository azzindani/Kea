import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def to_datetime(file_path: str, columns: List[str], output_path: str, format: Optional[str] = None, errors: str = 'coerce') -> str:
    """Convert columns to datetime."""
    df = load_dataframe(file_path)
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format=format, errors=errors)
    save_dataframe(df, output_path)
    return f"Converted columns {columns} to datetime. Saved to {output_path}"

def resample_data(file_path: str, rule: str, on: Optional[str] = None, index_col: Optional[str] = None, agg: Dict[str, Union[str, List[str]]] = None, output_path: str = "") -> str:
    """
    Resample time-series data.
    rule: 'D', 'M', 'H', '5T', etc.
    agg: {"col": "mean"}
    """
    df = load_dataframe(file_path)
    
    # Set index if provided
    if index_col:
        df = df.set_index(index_col)
    elif on:
        df = df.set_index(on)
        
    if not isinstance(df.index, pd.DatetimeIndex):
         # Try to convert index if it's not datetime
         df.index = pd.to_datetime(df.index)

    if agg is None:
        # Default to mean for numeric cols if no agg provided
        resampled = df.resample(rule).mean()
    else:
        resampled = df.resample(rule).agg(agg)
        
        # Flatten multi-index columns if present
        if isinstance(resampled.columns, pd.MultiIndex):
            resampled.columns = ['_'.join(col).strip() for col in resampled.columns.values]

    resampled = resampled.reset_index()
    save_dataframe(resampled, output_path)
    return f"Resampled data (rule={rule}) saved to {output_path}"

def rolling_window(file_path: str, window: int, agg: str, on: Optional[str] = None, columns: Optional[List[str]] = None, output_path: str = "") -> str:
    """
    Apply rolling window calculation.
    agg: 'mean', 'sum', 'std', 'min', 'max'
    """
    df = load_dataframe(file_path)
    
    # If 'on' is specified, we don't set it as index, we just sort by it to be safe? 
    # Usually rolling is done on index or just order. Let's assume order or explicit sort.
    if on:
        df = df.sort_values(by=on)
        
    target_cols = columns if columns else df.select_dtypes(include='number').columns.tolist()
    
    # We will create NEW columns for the rolling values
    for col in target_cols:
        new_col_name = f"{col}_rolling_{window}_{agg}"
        roller = df[col].rolling(window=window)
        if agg == 'mean':
            df[new_col_name] = roller.mean()
        elif agg == 'sum':
            df[new_col_name] = roller.sum()
        elif agg == 'std':
            df[new_col_name] = roller.std()
        elif agg == 'min':
            df[new_col_name] = roller.min()
        elif agg == 'max':
            df[new_col_name] = roller.max()
            
    save_dataframe(df, output_path)
    return f"Added rolling {agg} (window={window}) to {target_cols}. Saved to {output_path}"

def shift_diff(file_path: str, periods: int, columns: List[str], operation: str, output_path: str) -> str:
    """
    Shift or Diff data.
    operation: 'shift' (lag/lead) or 'diff' (difference)
    """
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        
        if operation == 'shift':
            new_col = f"{col}_shift_{periods}"
            df[new_col] = df[col].shift(periods)
        elif operation == 'diff':
            new_col = f"{col}_diff_{periods}"
            df[new_col] = df[col].diff(periods)
            
    save_dataframe(df, output_path)
    return f"Applied {operation} (periods={periods}) to {columns}. Saved to {output_path}"

def dt_accessor(file_path: str, column: str, component: str, output_path: str) -> str:
    """
    Extract datetime component.
    component: 'year', 'month', 'day', 'hour', 'minute', 'second', 'weekday', 'quarter'
    """
    df = load_dataframe(file_path)
    
    # Ensure it's datetime
    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        df[column] = pd.to_datetime(df[column], errors='coerce')
        
    new_col = f"{column}_{component}"
    
    series = df[column].dt
    if component == 'year': df[new_col] = series.year
    elif component == 'month': df[new_col] = series.month
    elif component == 'day': df[new_col] = series.day
    elif component == 'hour': df[new_col] = series.hour
    elif component == 'minute': df[new_col] = series.minute
    elif component == 'second': df[new_col] = series.second
    elif component == 'weekday': df[new_col] = series.weekday
    elif component == 'quarter': df[new_col] = series.quarter
    elif component == 'date': df[new_col] = series.date
    elif component == 'time': df[new_col] = series.time
    
    save_dataframe(df, output_path)
    return f"Extracted {component} from {column}. Saved to {output_path}"
