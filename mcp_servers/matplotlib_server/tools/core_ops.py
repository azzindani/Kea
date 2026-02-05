import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import io
import base64
import json
import structlog
from typing import Any, List, Union, Optional, Dict, Tuple

# Use non-interactive backend
matplotlib.use('Agg')

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

def get_figure_as_base64(fig=None, format='png', dpi=100) -> str:
    """Save the current or passed figure to base64 string."""
    if fig is None:
        fig = plt.gcf()
    
    buf = io.BytesIO()
    fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig) # Clear memory
    return data

def setup_figure(title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, figsize: Tuple[int, int] = (10, 6)):
    """Setup a new figure with common attributes."""
    fig, ax = plt.subplots(figsize=figsize)
    if title: ax.set_title(title)
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    return fig, ax
