import pandas as pd
from typing import Optional, Dict, Any, List, Union
from mcp_servers.pandas_server.utils import load_dataframe

def inspect_head(file_path: str, n: int = 5) -> List[Dict[str, Any]]:
    """Return the first n rows."""
    df = load_dataframe(file_path)
    return df.head(n).to_dict(orient='records')

def inspect_tail(file_path: str, n: int = 5) -> List[Dict[str, Any]]:
    """Return the last n rows."""
    df = load_dataframe(file_path)
    return df.tail(n).to_dict(orient='records')

def inspect_columns(file_path: str) -> List[str]:
    """Return list of column names."""
    df = load_dataframe(file_path)
    return list(df.columns)

def inspect_dtypes(file_path: str) -> Dict[str, str]:
    """Return column data types."""
    df = load_dataframe(file_path)
    return {k: str(v) for k, v in df.dtypes.items()}

def inspect_describe(file_path: str, include: Optional[str] = None) -> Dict[str, Any]:
    """Return summary statistics."""
    df = load_dataframe(file_path)
    # Convert 'all' string to actual 'all' literal if needed, or pass None for default
    inc = 'all' if include == 'all' else None
    desc = df.describe(include=inc)
    # The result of describe() is a DataFrame, convert to dict
    return desc.to_dict()

def inspect_value_counts(file_path: str, column: str, n: int = 10) -> Dict[str, int]:
    """Return value counts for a specific column."""
    df = load_dataframe(file_path)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset")
    return df[column].value_counts().head(n).to_dict()

def inspect_shape(file_path: str) -> tuple:
    """Return (rows, cols)."""
    df = load_dataframe(file_path)
    return df.shape
