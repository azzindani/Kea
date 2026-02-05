import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def calculate_zscore(file_path: str, columns: List[str], output_path: str) -> str:
    """Calculate Z-Score for columns."""
    df = load_dataframe(file_path)
    
    for col in columns:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            new_col = f"{col}_zscore"
            df[new_col] = (df[col] - mean) / std
            
    save_dataframe(df, output_path)
    return f"Calculated Z-Scores for {columns}. Saved to {output_path}"

def rank_data(file_path: str, column: str, method: str = "average", ascending: bool = True, output_path: str = "") -> str:
    """rank: 'average', 'min', 'max', 'first', 'dense'."""
    df = load_dataframe(file_path)
    new_col = f"{column}_rank"
    df[new_col] = df[column].rank(method=method, ascending=ascending)
    save_dataframe(df, output_path)
    return f"Ranked {column} (method={method}). Saved to {output_path}"

def quantile(file_path: str, column: str, q: float, output_path: str = "") -> Dict[str, Any]:
    """Calculate value at quantile q (e.g. 0.95). Does not modify dataset unless requested? No, usually just returns value."""
    # This might be an inspection tool, but fitting here is fine.
    # Actually let's return it as a string message and maybe save if desired?
    # Let's keep it consistent: tools return a success message or data preview. 
    # For a transformation, we might want to FILTER by quantile?
    # Let's stick to calculating and returning the value in the text or as a dict for the LLM.
    df = load_dataframe(file_path)
    val = df[column].quantile(q)
    return {"column": column, "quantile": q, "value": float(val)}

def correlation_matrix(file_path: str, method: str = "pearson") -> Dict[str, Any]:
    """Get correlation matrix."""
    df = load_dataframe(file_path)
    corr = df.corr(method=method)
    return corr.to_dict()
    
def clip_values(file_path: str, columns: List[str], lower: Optional[float] = None, upper: Optional[float] = None, output_path: str = "") -> str:
    """Clip values to bounds."""
    df = load_dataframe(file_path)
    df[columns] = df[columns].clip(lower=lower, upper=upper)
    save_dataframe(df, output_path)
    return f"Clipped {columns} to [{lower}, {upper}]. Saved to {output_path}"
