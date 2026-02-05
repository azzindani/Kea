import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe

def filter_data(file_path: str, query: str, output_path: str) -> str:
    """Filter rows using DataFrame.query()."""
    df = load_dataframe(file_path)
    filtered_df = df.query(query)
    save_dataframe(filtered_df, output_path)
    return f"Filtered data saved to {output_path}. Rows: {len(filtered_df)}"

def select_columns(file_path: str, columns: List[str], output_path: str) -> str:
    """Select specific columns."""
    df = load_dataframe(file_path)
    subset_df = df[columns]
    save_dataframe(subset_df, output_path)
    return f"Selected {len(columns)} columns saved to {output_path}"

def sort_data(file_path: str, by: Union[str, List[str]], ascending: bool, output_path: str) -> str:
    """Sort data by column(s)."""
    df = load_dataframe(file_path)
    sorted_df = df.sort_values(by=by, ascending=ascending)
    save_dataframe(sorted_df, output_path)
    return f"Sorted data saved to {output_path}"

def drop_duplicates(file_path: str, subset: Optional[List[str]], output_path: str) -> str:
    """Drop duplicate rows."""
    df = load_dataframe(file_path)
    cleaned_df = df.drop_duplicates(subset=subset)
    save_dataframe(cleaned_df, output_path)
    return f"Data with duplicates removed saved to {output_path}. Rows: {len(cleaned_df)}"

def fill_na(file_path: str, value: Any, output_path: str, method: Optional[str] = None) -> str:
    """Fill missing values."""
    df = load_dataframe(file_path)
    if method:
        filled_df = df.fillna(method=method)
    else:
        filled_df = df.fillna(value=value)
    save_dataframe(filled_df, output_path)
    return f"Data with filled NAs saved to {output_path}"

def sample_data(file_path: str, n: Optional[int] = None, frac: Optional[float] = None, output_path: str = "") -> str:
    """Sample random rows."""
    df = load_dataframe(file_path)
    sampled_df = df.sample(n=n, frac=frac)
    save_dataframe(sampled_df, output_path)
    return f"Sampled data saved to {output_path}. Rows: {len(sampled_df)}"

def astype(file_path: str, column_types: Dict[str, str], output_path: str) -> str:
    """Convert column types. types: 'int', 'float', 'str', 'datetime', 'category'."""
    df = load_dataframe(file_path)
    df = df.astype(column_types)
    save_dataframe(df, output_path)
    return f"Converted types: {column_types}. Saved to {output_path}"

def rename_columns(file_path: str, mapping: Dict[str, str], output_path: str) -> str:
    """Rename columns using a mapping dict."""
    df = load_dataframe(file_path)
    df = df.rename(columns=mapping)
    save_dataframe(df, output_path)
    return f"Renamed columns. Saved to {output_path}"

def set_index(file_path: str, columns: Union[str, List[str]], drop: bool = True, output_path: str = "") -> str:
    """Set one or more columns as index."""
    df = load_dataframe(file_path)
    df = df.set_index(columns, drop=drop)
    save_dataframe(df, output_path)
    return f"Set index to {columns}. Saved to {output_path}"

def reset_index(file_path: str, drop: bool = False, output_path: str = "") -> str:
    """Reset index to columns."""
    df = load_dataframe(file_path)
    df = df.reset_index(drop=drop)
    save_dataframe(df, output_path)
    return f"Reset index. Saved to {output_path}"

