import pandas as pd
import numpy as np
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def conditional_mask(file_path: str, condition: str, value_if_true: Any, value_if_false: Any, output_path: str, column: Optional[str] = None) -> str:
    """
    Apply arithmetic or replacement based on condition.
    If column is None, operates on entire dataframe (useful for masking).
    If condition is a string query (e.g. "age > 50"), we use eval/query style internally or np.where.
    For simplicity and safety, let's use DataFrame.eval logic or manual column application.
    """
    df = load_dataframe(file_path)
    
    # We will assume condition is a string evaluable by df.eval()
    mask = df.eval(condition)
    
    if column:
        # Update specific column
        # np.where(condition, x, y)
        # Note: value_if_true/false might be column names or literals. 
        # This is complex to parse perfectly safely. 
        # Simplest approach: Use pandas mask/where
        
        # df[col].where(cond, other) replaces values where condition is FALSE.
        # df[col].mask(cond, other) replaces values where condition is TRUE.
        
        # Let's say user wants: if age > 10, set 'status' to 'adult', else 'child'
        # df['status'] = np.where(df.eval("age > 10"), "adult", "child")
        
        df[column] = np.where(mask, value_if_true, value_if_false)
        
    else:
        # Apply to whole frame? Rare. Usually we create a new column or update one.
        # Let's force column usage for now to be safe.
        raise ValueError("Must specify target 'column' to update.")
        
    save_dataframe(df, output_path)
    return f"Applied conditional logic on {column} based on '{condition}'. Saved to {output_path}"

def isin_filter(file_path: str, column: str, values: List[Any], keep: bool = True, output_path: str = "") -> str:
    """Filter rows where column is IN values (or NOT IN if keep=False)."""
    df = load_dataframe(file_path)
    
    mask = df[column].isin(values)
    if not keep:
        mask = ~mask
        
    df = df[mask]
    save_dataframe(df, output_path)
    return f"Filtered by isin (keep={keep}). Rows: {len(df)}. Saved to {output_path}"

def compare_datasets(left_path: str, right_path: str) -> Dict[str, Any]:
    """Compare two dataframes and return report."""
    left = load_dataframe(left_path)
    right = load_dataframe(right_path)
    
    try:
        comparison = left.compare(right)
        return {
            "status": "success",
            "diff_shape": comparison.shape,
            "differences_found": len(comparison) > 0,
            "preview": comparison.head(5).to_dict(orient='records')
        }
    except ValueError as e:
        return {"status": "error", "message": str(e), "hint": "DataFrames must have identical index and columns to compare."}
