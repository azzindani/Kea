import seaborn as sns
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

def get_figure_as_base64(obj=None, format='png', dpi=100) -> str:
    """Save the current or passed figure/grid to base64 string."""
    # Seaborn objects (FacetGrid, PairGrid, JointGrid) have 'savefig' method
    # Or 'fig' attribute
    if hasattr(obj, 'savefig'):
        buf = io.BytesIO()
        obj.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        plt.close(obj.fig) # Close the figure contained
    elif hasattr(obj, 'figure'):
        # Axes object
        fig = obj.figure
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    elif isinstance(obj, matplotlib.figure.Figure):
        fig = obj
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    else:
        # Fallback to current figure
        fig = plt.gcf()
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    return data

def setup_style(style: str = "whitegrid", palette: str = "viridis"):
    """Setup global seaborn style."""
    sns.set_theme(style=style, palette=palette)
