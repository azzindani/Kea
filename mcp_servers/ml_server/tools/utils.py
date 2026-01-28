import pandas as pd
from typing import Any, Union, List, Dict

def load_dataframe(data_url: str = None, data: Union[Dict, List] = None) -> pd.DataFrame:
    """Load DataFrame from URL or inline data."""
    if data_url:
        return pd.read_csv(data_url)
    elif data:
        if isinstance(data, dict) and "columns" in data and "rows" in data:
            return pd.DataFrame(data["rows"], columns=data["columns"])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError("Invalid data format. Expected {columns: [], rows: []} or list of dicts")
    else:
        raise ValueError("Either data_url or data must be provided")

def format_result(title: str, content: str) -> str:
    """Format markdown result."""
    return f"# {title}\n\n{content}"
