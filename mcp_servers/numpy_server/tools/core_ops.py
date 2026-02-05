import numpy as np
import structlog
from typing import Any, List, Union, Optional
import json

logger = structlog.get_logger()

# Common type for numerical input
NumericData = Union[List[float], List[int], str] 

def parse_array(data: NumericData, dtype: Optional[str] = None) -> np.ndarray:
    """
    Parse input data into a numpy array safely.
    Accepts: List, String (JSON or CSV-like).
    """
    try:
        final_dtype = None
        if dtype:
            try:
                final_dtype = getattr(np, dtype)
            except AttributeError:
                pass # Fallback to default inference

        if isinstance(data, str):
            # Try JSON first
            try:
                parsed = json.loads(data)
                return np.array(parsed, dtype=final_dtype)
            except json.JSONDecodeError:
                # Try simple comma-separated
                if "," in data:
                    return np.array([float(x.strip()) for x in data.split(",")], dtype=final_dtype)
                # Try space separated
                return np.array([float(x.strip()) for x in data.split()], dtype=final_dtype)
        
        return np.array(data, dtype=final_dtype)
    except Exception as e:
        logger.error("data_parsing_failed", error=str(e))
        raise ValueError(f"Could not parse input data to numpy array: {str(e)}")

def to_serializable(data: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, (np.floating, float)):
        return float(data)
    elif isinstance(data, (np.bool_, bool)):
        return bool(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_serializable(v) for v in data]
    elif data is None:
        return None
    return str(data)
