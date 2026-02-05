import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def explode_list(file_path: str, column: str, output_path: str) -> str:
    """Explode a column containing lists into separate rows."""
    df = load_dataframe(file_path)
    df = df.explode(column)
    save_dataframe(df, output_path)
    return f"Exploded list column {column}. Rows: {len(df)}. Saved to {output_path}"

def flatten_json(file_path: str, column: str, output_path: str, sep: str = "_") -> str:
    """Normalize a semi-structured JSON column into flat columns."""
    df = load_dataframe(file_path)
    
    # Check if column exists
    if column not in df.columns:
        raise ValueError(f"Column {column} not found")
        
    # We assume the column contains dicts or json strings. 
    # If strings, we might need to parse them first? 
    # Let's assume they are already dicts/objects if loaded from JSON/Parquet, 
    # or strings if loaded from CSV.
    
    # Try to ensure they are dicts
    sample = df[column].dropna().iloc[0] if not df[column].dropna().empty else None
    if isinstance(sample, str):
        import json
        # Apply strict parsing, or lenient?
        try:
             df[column] = df[column].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        except Exception:
             pass # Maybe it's not valid JSON, proceed and let pd.json_normalize fail or handle it

    # Normalize
    # records must be a list of dicts.
    records = df[column].tolist()
    normalized = pd.json_normalize(records, sep=sep)
    
    # Prefix normalized columns to avoid collision with existing
    normalized.columns = [f"{column}{sep}{c}" for c in normalized.columns]
    
    # Concatenate back
    df = df.drop(columns=[column])
    df = pd.concat([df.reset_index(drop=True), normalized.reset_index(drop=True)], axis=1)
    
    save_dataframe(df, output_path)
    return f"Flattened JSON column {column} into {len(normalized.columns)} new columns. Saved to {output_path}"

def stack_unstack(file_path: str, operation: str, level: Union[int, str, List[str]] = -1, output_path: str = "") -> str:
    """
    Reshape data using stack/unstack.
    operation: 'stack' or 'unstack'
    """
    df = load_dataframe(file_path)
    
    if operation == 'stack':
        df = df.stack(level=level)
    elif operation == 'unstack':
        df = df.unstack(level=level)
    else:
        raise ValueError("Operation must be 'stack' or 'unstack'")
        
    # Result might be Series or DataFrame with MultiIndex. 
    # To save properly, we often need to reset index.
    if isinstance(df, pd.Series):
        df = df.to_frame()
        
    df = df.reset_index()
    save_dataframe(df, output_path)
    return f"Applied {operation} (level={level}). Saved to {output_path}"

def cross_join(left_path: str, right_path: str, output_path: str) -> str:
    """Compute Cartesian product of two datasets."""
    left = load_dataframe(left_path)
    right = load_dataframe(right_path)
    
    merged = pd.merge(left, right, how='cross')
    save_dataframe(merged, output_path)
    return f"Cross join complete. Shape: {merged.shape}. Saved to {output_path}"
