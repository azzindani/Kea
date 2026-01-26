import pandas as pd
import numpy as np
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def create_interactions(file_path: str, features: List[str], operations: List[str], output_path: str) -> str:
    """
    Create interaction features (A*B, A/B).
    features: List of numeric columns [A, B, C] -> Interactions pairs.
    operations: ['mul', 'div', 'add', 'sub']
    """
    df = load_dataframe(file_path)
    import itertools
    
    created = []
    
    for a, b in itertools.combinations(features, 2):
        if a not in df.columns or b not in df.columns: continue
        
        for op in operations:
            name = f"{a}_{op}_{b}"
            if op == 'mul':
                df[name] = df[a] * df[b]
            elif op == 'div':
                df[name] = df[a] / (df[b].replace(0, np.nan)) # Safe div
            elif op == 'add':
                df[name] = df[a] + df[b]
            elif op == 'sub':
                df[name] = df[a] - df[b]
            created.append(name)
            
    save_dataframe(df, output_path)
    return f"Created {len(created)} interaction features. Saved to {output_path}"

def polynomial_features(file_path: str, columns: List[str], degree: int, output_path: str) -> str:
    """Create polynomial features (x^2, x^3...)."""
    df = load_dataframe(file_path)
    
    for col in columns:
        if col not in df.columns: continue
        for d in range(2, degree + 1):
            df[f"{col}_poly_{d}"] = df[col] ** d
            
    save_dataframe(df, output_path)
    return f"Created polynomial features (degree={degree}) for {columns}. Saved to {output_path}"
