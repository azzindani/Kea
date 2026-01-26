import pandas as pd
import numpy as np
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def apply_math(file_path: str, columns: List[str], func: str, output_path: str, new_col_prefix: str = "") -> str:
    """
    Apply mathematical function to columns.
    func: 'log', 'log1p', 'exp', 'sqrt', 'abs', 'round', 'floor', 'ceil'
    """
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        
        prefix = new_col_prefix if new_col_prefix else f"{col}_"
        # If no prefix provided and we don't want to overwrite, usually we suffix? 
        # But 'log' is distinct. Let's use suffix for clarity: col_log
        new_col = f"{col}_{func}" if not new_col_prefix else f"{new_col_prefix}{col}"
        
        if func == 'log':
            df[new_col] = np.log(df[col])
        elif func == 'log1p':
            df[new_col] = np.log1p(df[col])
        elif func == 'exp':
            df[new_col] = np.exp(df[col])
        elif func == 'sqrt':
            df[new_col] = np.sqrt(df[col])
        elif func == 'abs':
            df[new_col] = np.abs(df[col])
        elif func == 'round':
            df[new_col] = np.round(df[col])
        elif func == 'floor':
            df[new_col] = np.floor(df[col])
        elif func == 'ceil':
            df[new_col] = np.ceil(df[col])
            
    save_dataframe(df, output_path)
    return f"Applied {func} to {columns}. Saved to {output_path}"

def normalize_minmax(file_path: str, columns: List[str], output_path: str, feature_range: tuple = (0, 1)) -> str:
    """Scale data to [min, max] range (default 0-1)."""
    df = load_dataframe(file_path)
    
    min_val, max_val = feature_range
    
    for col in columns:
        if col not in df.columns: continue
        
        col_min = df[col].min()
        col_max = df[col].max()
        
        if col_max == col_min:
            df[f"{col}_scaled"] = 0 # Avoid div by zero
        else:
            std = (df[col] - col_min) / (col_max - col_min)
            df[f"{col}_scaled"] = std * (max_val - min_val) + min_val
            
    save_dataframe(df, output_path)
    return f"MinMax Scaled {columns} to {feature_range}. Saved to {output_path}"

def standardize_scale(file_path: str, columns: List[str], output_path: str) -> str:
    """Standardize data (Mean=0, Std=1)."""
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        
        mean = df[col].mean()
        std = df[col].std()
        
        df[f"{col}_std_scaled"] = (df[col] - mean) / std
            
    save_dataframe(df, output_path)
    return f"Standardized {columns}. Saved to {output_path}"

def calc_stats_vector(file_path: str, columns: List[str], func: str) -> Dict[str, float]:
    """Calculate vector norms/stats. func: 'norm_l1', 'norm_l2'."""
    df = load_dataframe(file_path)
    stats = {}
    
    for col in columns:
        if col not in df.columns: continue
        val = 0.0
        if func == 'norm_l1':
            val = np.sum(np.abs(df[col]))
        elif func == 'norm_l2':
            val = np.sqrt(np.sum(df[col]**2))
        stats[col] = float(val)
        
    return stats
