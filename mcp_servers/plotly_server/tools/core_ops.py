import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import io
import base64
import json
import structlog
from typing import Any, List, Union, Optional, Dict, Tuple

logger = structlog.get_logger()

# Set default template
pio.templates.default = "plotly_white"

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

def get_figure_output(fig: go.Figure, format: str = 'png', width: int = 1000, height: int = 600, scale: int = 2) -> str:
    """
    Return figure as Base64 string (for png/jpeg) or JSON string (for interactive).
    Formats: 'png', 'jpeg', 'svg', 'json'.
    """
    if format == 'json':
        return pio.to_json(fig)
    
    # For static images, we use pio.to_image (requires kaleido)
    try:
        img_bytes = pio.to_image(fig, format=format, width=width, height=height, scale=scale)
        return base64.b64encode(img_bytes).decode('utf-8')
    except ValueError as e:
        # Fallback if kaleido not installed/working, return JSON
        logger.warning(f"Static image generation failed: {e}. Returning JSON.")
        return pio.to_json(fig)
