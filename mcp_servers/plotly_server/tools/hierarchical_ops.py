from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_sunburst(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a sunburst chart."""
    df = parse_data_frame(data)
    fig = px.sunburst(df, path=path, values=values, color=color, title=title)
    return get_figure_output(fig, format=format)

async def plot_treemap(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a treemap chart."""
    df = parse_data_frame(data)
    fig = px.treemap(df, path=path, values=values, color=color, title=title)
    return get_figure_output(fig, format=format)

async def plot_icicle(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create an icicle chart."""
    df = parse_data_frame(data)
    fig = px.icicle(df, path=path, values=values, color=color, title=title)
    return get_figure_output(fig, format=format)
