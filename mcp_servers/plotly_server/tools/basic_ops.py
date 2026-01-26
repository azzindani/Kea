from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_scatter(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a scatter plot."""
    df = parse_data_frame(data)
    fig = px.scatter(df, x=x, y=y, color=color, size=size, title=title)
    return get_figure_output(fig, format=format)

async def plot_line(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a line plot."""
    df = parse_data_frame(data)
    fig = px.line(df, x=x, y=y, color=color, markers=markers, title=title)
    return get_figure_output(fig, format=format)

async def plot_bar(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, barmode: str = 'relative', title: Optional[str] = None, format: str = 'png') -> str:
    """Create a bar chart. barmode: 'group', 'overlay', 'relative'."""
    df = parse_data_frame(data)
    fig = px.bar(df, x=x, y=y, color=color, barmode=barmode, title=title)
    return get_figure_output(fig, format=format)

async def plot_pie(data: DataInput, names: str, values: str, hole: float = 0.0, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a pie chart (or donut if hole > 0)."""
    df = parse_data_frame(data)
    fig = px.pie(df, names=names, values=values, hole=hole, title=title)
    return get_figure_output(fig, format=format)
