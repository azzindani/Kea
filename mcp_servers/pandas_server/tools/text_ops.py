import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def str_split(file_path: str, column: str, pat: Optional[str] = None, expand: bool = True, output_path: str = "") -> str:
    """Split string column."""
    df = load_dataframe(file_path)
    
    # Ensure valid string col
    if column not in df.columns:
        raise ValueError(f"Column {column} not found")
        
    result = df[column].astype(str).str.split(pat=pat, expand=expand)
    
    if expand:
        # If expand=True, it returns a DF. We need to merge it back or rename columns
        prefix = f"{column}_split_"
        result.columns = [f"{prefix}{i}" for i in range(result.shape[1])]
        df = pd.concat([df, result], axis=1)
    else:
        df[f"{column}_split"] = result
        
    save_dataframe(df, output_path)
    return f"Split column {column} into {result.shape[1] if expand else 1} parts. Saved to {output_path}"

def str_replace(file_path: str, column: str, pat: str, repl: str, regex: bool = False, output_path: str = "") -> str:
    """Replace occurrences in string."""
    df = load_dataframe(file_path)
    df[column] = df[column].astype(str).str.replace(pat, repl, regex=regex)
    save_dataframe(df, output_path)
    return f"Replaced '{pat}' with '{repl}' in {column}. Saved to {output_path}"

def str_extract(file_path: str, column: str, pat: str, output_path: str = "") -> str:
    """Extract capture groups using regex."""
    df = load_dataframe(file_path)
    extracted = df[column].astype(str).str.extract(pat)
    
    # Rename extracted columns to avoid collision if possible, or leave as numbers/names from regex
    # We'll prefix them
    extracted.columns = [f"{column}_extract_{col}" for col in extracted.columns]
    
    df = pd.concat([df, extracted], axis=1)
    save_dataframe(df, output_path)
    return f"Extracted patterns from {column}. Saved to {output_path}"

def str_case(file_path: str, column: str, case: str, output_path: str = "") -> str:
    """Convert case: 'lower', 'upper', 'title', 'capitalize'."""
    df = load_dataframe(file_path)
    s = df[column].astype(str).str
    
    if case == 'lower': df[column] = s.lower()
    elif case == 'upper': df[column] = s.upper()
    elif case == 'title': df[column] = s.title()
    elif case == 'capitalize': df[column] = s.capitalize()
    
    save_dataframe(df, output_path)
    return f"Converted {column} to {case} case. Saved to {output_path}"

def str_contains(file_path: str, column: str, pat: str, regex: bool = False, output_path: str = "") -> str:
    """Create boolean mask for string containment."""
    df = load_dataframe(file_path)
    new_col = f"{column}_contains_{pat}"
    # Sanitizing path for column name might be needed, but let's keep it simple
    new_col = "".join(c for c in new_col if c.isalnum() or c == '_')
    
    df[new_col] = df[column].astype(str).str.contains(pat, regex=regex)
    save_dataframe(df, output_path)
    return f"Created mask column {new_col}. Saved to {output_path}"
