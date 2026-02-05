import xgboost as xgb
import pandas as pd
import numpy as np
import structlog
import json
import io
import joblib
import base64
from typing import Any, List, Union, Optional, Dict, Tuple

logger = structlog.get_logger()

# Common Types
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

def parse_data_frame(data: DataInput) -> pd.DataFrame:
    """Parse input data into a Pandas DataFrame."""
    try:
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return pd.DataFrame(parsed)
                elif isinstance(parsed, dict) and 'data' in parsed:
                    return pd.DataFrame(**parsed)
                return pd.DataFrame(parsed)
            except json.JSONDecodeError:
                # Try CSV-like
                if "," in data or "\n" in data:
                    return pd.read_csv(io.StringIO(data))
                try:
                    return pd.DataFrame(json.loads(data))
                except:
                    pass
        return pd.DataFrame(data)
    except Exception as e:
        raise ValueError(f"Could not parse input data to DataFrame: {str(e)}")

def parse_vector(data: VectorInput) -> Optional[pd.Series]:
    """Parse 1D input into a Pandas Series."""
    if data is None: return None
    try:
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return pd.Series(parsed)
            except:
                if "," in data:
                     return pd.Series([x.strip() for x in data.split(",")])
        return pd.Series(data)
    except Exception as e:
         raise ValueError(f"Could not parse input data to Series: {str(e)}")

def create_dmatrix(data: DataInput, label: Optional[VectorInput] = None, weight: Optional[VectorInput] = None) -> xgb.DMatrix:
    """Create a DMatrix from input data."""
    df = parse_data_frame(data)
    y = parse_vector(label)
    w = parse_vector(weight)
    
    return xgb.DMatrix(df, label=y, weight=w)

def serialize_booster(booster: Union[xgb.Booster, Any]) -> str:
    """Serialize a Booster or Sklearn Wrapper to base64 string."""
    buffer = io.BytesIO()
    joblib.dump(booster, buffer)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def deserialize_booster(model_str: str) -> Any:
    """Deserialize a Booster or Wrapper from base64 string."""
    buffer = io.BytesIO(base64.b64decode(model_str.encode('utf-8')))
    return joblib.load(buffer)

def to_serializable(data: Any) -> Any:
    """Convert Numpy/Pandas types to Python native types."""
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return json.loads(data.to_json(orient='records'))
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
