import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def one_hot_encode(file_path: str, columns: List[str], output_path: str, drop_first: bool = False, prefix_sep: str = "_") -> str:
    """One-hot encode categorical variables."""
    df = load_dataframe(file_path)
    
    encoded = pd.get_dummies(df, columns=columns, drop_first=drop_first, prefix_sep=prefix_sep)
    
    save_dataframe(encoded, output_path)
    return f"One-hot encoded {columns}. New shape: {encoded.shape}. Saved to {output_path}"

def bin_data(file_path: str, column: str, bins: Union[int, List[float]], labels: Optional[List[str]] = None, method: str = 'cut', output_path: str = "") -> str:
    """
    Discretize continuous data.
    method: 'cut' (equal width) or 'qcut' (equal frequency/quantile based)
    """
    df = load_dataframe(file_path)
    
    new_col = f"{column}_binned"
    
    if method == 'cut':
        df[new_col] = pd.cut(df[column], bins=bins, labels=labels)
    elif method == 'qcut':
        # bins must be int or stats
        if isinstance(bins, list): 
             # qcut uses q kwarg, which expects fractions if provided as list
             df[new_col] = pd.qcut(df[column], q=bins, labels=labels)
        else:
             df[new_col] = pd.qcut(df[column], q=bins, labels=labels)
             
    # Convert category to str for serialization safety usually
    if df[new_col].dtype.name == 'category':
        df[new_col] = df[new_col].astype(str)
        
    save_dataframe(df, output_path)
    return f"Binned {column} into {new_col}. Saved to {output_path}"

def factorize_col(file_path: str, column: str, output_path: str) -> str:
    """Encode object as enumerated type / integers."""
    df = load_dataframe(file_path)
    
    codes, uniques = pd.factorize(df[column])
    df[f"{column}_factorized"] = codes
    
    save_dataframe(df, output_path)
    return f"Factorized {column}. Unique values: {len(uniques)}. Saved to {output_path}"
