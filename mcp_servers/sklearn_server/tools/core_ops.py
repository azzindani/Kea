import pandas as pd
import numpy as np
import structlog
import json
import io
import joblib
import base64
from typing import Any, List, Union, Optional, Dict

logger = structlog.get_logger()

# Common Types
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

def parse_data(data: DataInput) -> pd.DataFrame:
    """
    Parse input data into a Pandas DataFrame.
    Supports JSON records, CSV string, or List of Lists.
    """
    try:
        if isinstance(data, str):
            # Try JSON first
            try:
                parsed = json.loads(data)
                # JSON can be list of dicts (records) or dict of lists
                if isinstance(parsed, list):
                    return pd.DataFrame(parsed)
                elif isinstance(parsed, dict) and 'data' in parsed:
                    # split format
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
                
                # Try simple list string
                try:
                    return pd.DataFrame(json.loads(data))
                except:
                    pass
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error("data_parsing_failed", error=str(e))
        raise ValueError(f"Could not parse input data to DataFrame: {str(e)}")

def parse_vector(data: VectorInput) -> pd.Series:
    """Parse 1D input into a Pandas Series."""
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

# Model Persistence (In-Memory for simplicity in stateless MCP, or base64 for passing?)
# Since MCP tools are stateless, we can't easily "hold" a model in memory between tool calls 
# unless we use a global store (which resets on restart) or pass model state.
# For specialized "Pipeline Runner" tools, we train and predict in one go.
# For separate training/prediction, we can return the model as a base64 pickle string.

def serialize_model(model: Any) -> str:
    """Serialize a model to base64 string."""
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def deserialize_model(model_str: str) -> Any:
    """Deserialize a model from base64 string."""
    buffer = io.BytesIO(base64.b64decode(model_str.encode('utf-8')))
    return joblib.load(buffer)
