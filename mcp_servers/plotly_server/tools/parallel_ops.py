from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_parallel_coordinates(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a parallel coordinates plot for multi-dimensional numerical data."""
    df = parse_data_frame(data)
    fig = px.parallel_coordinates(df, dimensions=dimensions, color=color, title=title)
    return get_figure_output(fig, format=format)

async def plot_parallel_categories(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a parallel categories plot for multi-dimensional categorical data."""
    df = parse_data_frame(data)
    fig = px.parallel_categories(df, dimensions=dimensions, color=color, title=title)
    return get_figure_output(fig, format=format)
