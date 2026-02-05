from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_scatter_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a polar scatter plot."""
    df = parse_data_frame(data)
    fig = px.scatter_polar(df, r=r, theta=theta, color=color, size=size, title=title)
    return get_figure_output(fig, format=format)

async def plot_line_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, line_close: bool = True, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a polar line plot (radar chart)."""
    df = parse_data_frame(data)
    fig = px.line_polar(df, r=r, theta=theta, color=color, line_close=line_close, title=title)
    return get_figure_output(fig, format=format)

async def plot_bar_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a polar bar chart (wind rose)."""
    df = parse_data_frame(data)
    fig = px.bar_polar(df, r=r, theta=theta, color=color, title=title)
    return get_figure_output(fig, format=format)
