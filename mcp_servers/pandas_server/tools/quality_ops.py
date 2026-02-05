import pandas as pd
import numpy as np
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def validate_schema(file_path: str, required_columns: List[str], types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Validate existence of columns and optional types."""
    df = load_dataframe(file_path)
    missing = [c for c in required_columns if c not in df.columns]
    type_mismatches = {}
    
    if types:
        for col, expected_type in types.items():
            if col in df.columns:
                # Simple check using string representation of dtype
                if expected_type not in str(df[col].dtype):
                    type_mismatches[col] = f"Expected {expected_type}, got {df[col].dtype}"
                    
    valid = len(missing) == 0 and len(type_mismatches) == 0
    return {
        "valid": valid,
        "missing_columns": missing,
        "type_mismatches": type_mismatches
    }

def check_constraints(file_path: str, constraints: List[str]) -> Dict[str, Any]:
    """Check value constraints (e.g. 'age >= 0'). Returns count of violations."""
    df = load_dataframe(file_path)
    results = {}
    
    for constraint in constraints:
        # Constraint should evaluate to True if valid
        # We count False
        mask = df.eval(constraint)
        violations = (~mask).sum()
        results[constraint] = int(violations)
        
    return results

def remove_outliers_iqr(file_path: str, columns: List[str], factor: float = 1.5, output_path: str = "") -> str:
    """Remove rows with outliers based on IQR."""
    df = load_dataframe(file_path)
    initial_rows = len(df)
    
    mask = pd.Series([True] * len(df), index=df.index)
    
    for col in columns:
        if col not in df.columns: continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        col_mask = (df[col] >= (Q1 - factor * IQR)) & (df[col] <= (Q3 + factor * IQR))
        mask = mask & col_mask
        
    df_clean = df[mask]
    save_dataframe(df_clean, output_path)
    return f"Removed outliers (IQR factor={factor}). Rows reduced from {initial_rows} to {len(df_clean)}. Saved to {output_path}"

def drop_empty_cols(file_path: str, threshold: float = 1.0, output_path: str = "") -> str:
    """
    Drop columns with > threshold fraction of NaNs. 
    threshold=1.0 drops only all-NaN cols. 
    threshold=0.5 drops cols with >50% NaNs.
    """
    df = load_dataframe(file_path)
    
    rows = len(df)
    cols_to_drop = []
    
    for col in df.columns:
        na_count = df[col].isna().sum()
        if (na_count / rows) > threshold:
            cols_to_drop.append(col)
            
    df = df.drop(columns=cols_to_drop)
    save_dataframe(df, output_path)
    return f"Dropped {len(cols_to_drop)} columns exceeding {threshold*100}% NaN. Saved to {output_path}"
