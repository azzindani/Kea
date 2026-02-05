import pandas as pd
import numpy as np
import structlog
from typing import Any, List, Union, Optional, Dict
import json
import io

logger = structlog.get_logger()

# Common types
DataInput = Union[List[List[float]], List[Dict[str, Any]], str]
VectorInput = Union[List[float], str]

def parse_dataframe(data: DataInput) -> pd.DataFrame:
    """
    Parse input data into a Pandas DataFrame.
    Accepts: List of Lists, List of Dicts, JSON string, CSV string.
    """
    try:
        if isinstance(data, str):
            # Try JSON
            try:
                # Check for orient records or split
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return pd.DataFrame(parsed)
                elif isinstance(parsed, dict) and "data" in parsed:
                    # 'split' orientation: {'index': [], 'columns': [], 'data': []}
                    return pd.DataFrame(**parsed)
                else:
                    return pd.DataFrame(parsed)
            except json.JSONDecodeError:
                # Try CSV
                if "," in data or "\n" in data:
                    try:
                        return pd.read_csv(io.StringIO(data))
                    except:
                        pass
                
                # Try simple list string "[1, 2, 3]"
                try:
                    # Very simple fallback for single column
                    parsed = json.loads(data)
                    return pd.DataFrame(parsed)
                except:
                    pass
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error("dataframe_parsing_failed", error=str(e))
        raise ValueError(f"Could not parse input data to DataFrame: {str(e)}")

def parse_series(data: VectorInput, name: str = None) -> pd.Series:
    """Parse 1D input into a Pandas Series."""
    try:
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return pd.Series(parsed, name=name)
            except:
                if "," in data:
                     return pd.Series([float(x.strip()) for x in data.split(",")], name=name)
        
        return pd.Series(data, name=name)
    except Exception as e:
        raise ValueError(f"Could not parse input data to Series: {str(e)}")

def to_serializable(data: Any) -> Any:
    """Convert Pandas/Numpy types to Python native types."""
    if isinstance(data, (pd.DataFrame, pd.Series)):
        # Return as dict records for readability, or split for compactness?
        # Records is usually safest for general consumption
        # Handle nan
        return json.loads(data.to_json(orient='records')) # Quick way to handle NaNs->null
    elif isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, (np.floating, float)):
        return float(data) if not np.isnan(data) else None
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_serializable(v) for v in data]
    return data

def format_summary(model_res) -> str:
    """Extract summary as textTable."""
    return model_res.summary().as_text()
