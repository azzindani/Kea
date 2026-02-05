import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def group_by(file_path: str, by: Union[str, List[str]], agg: Dict[str, Union[str, List[str]]], output_path: str) -> str:
    """
    Group by column(s) and aggregate.
    agg example: {"col1": "sum", "col2": ["mean", "max"]}
    """
    df = load_dataframe(file_path)
    grouped = df.groupby(by).agg(agg)
    # Flatten multi-index columns if present
    if isinstance(grouped.columns, pd.MultiIndex):
         grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
    
    grouped = grouped.reset_index()
    save_dataframe(grouped, output_path)
    return f"Grouped data saved to {output_path}"

def merge_datasets(left_path: str, right_path: str, on: Union[str, List[str]], how: str, output_path: str) -> str:
    """Merge two datasets."""
    left = load_dataframe(left_path)
    right = load_dataframe(right_path)
    merged = pd.merge(left, right, on=on, how=how)
    save_dataframe(merged, output_path)
    return f"Merged data saved to {output_path}. Shape: {merged.shape}"

def concat_datasets(file_paths: List[str], axis: int, output_path: str) -> str:
    """Concatenate multiple datasets."""
    dfs = [load_dataframe(path) for path in file_paths]
    result = pd.concat(dfs, axis=axis)
    save_dataframe(result, output_path)
    return f"Concatenated data saved to {output_path}. Shape: {result.shape}"

def pivot_table(file_path: str, values: str, index: Union[str, List[str]], columns: Union[str, List[str]], aggfunc: str, output_path: str) -> str:
    """Create a pivot table."""
    df = load_dataframe(file_path)
    pivot = pd.pivot_table(df, values=values, index=index, columns=columns, aggfunc=aggfunc)
    pivot = pivot.reset_index()
    save_dataframe(pivot, output_path)
    return f"Pivot table saved to {output_path}"

def melt_data(file_path: str, id_vars: List[str], value_vars: Optional[List[str]], output_path: str) -> str:
    """Unpivot a DataFrame from wide to long format."""
    df = load_dataframe(file_path)
    melted = pd.melt(df, id_vars=id_vars, value_vars=value_vars)
    save_dataframe(melted, output_path)
    return f"Melted data saved to {output_path}"
