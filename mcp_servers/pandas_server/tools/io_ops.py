import pandas as pd
from typing import Optional, Dict, Any, List
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe, get_dataframe_info

def read_dataset(file_path: str, format: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Reads a dataset and returns its metadata and first few rows.
    Does NOT keep it in memory (stateless version).
    """
    df = load_dataframe(file_path, format=format, **kwargs)
    info = get_dataframe_info(df)
    head = df.head(5).to_dict(orient='records')
    
    return {
        "status": "success",
        "file_path": file_path,
        "info": info,
        "preview": head
    }

def convert_dataset(source_path: str, dest_path: str, source_format: Optional[str] = None, dest_format: Optional[str] = None, **kwargs) -> str:
    """
    Converts a dataset from one format to another.
    """
    df = load_dataframe(source_path, format=source_format)
    save_dataframe(df, dest_path, format=dest_format, **kwargs)
    return f"Successfully converted {source_path} to {dest_path}"

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Lightweight inspection without full load if possible, OR just load and inspect.
    For now, we load.
    """
    df = load_dataframe(file_path)
    return get_dataframe_info(df)
