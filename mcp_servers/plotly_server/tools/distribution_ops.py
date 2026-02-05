from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_histogram(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, nbins: Optional[int] = None, marginal: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a histogram. marginal: 'box', 'violin', 'rug'."""
    df = parse_data_frame(data)
    fig = px.histogram(df, x=x, y=y, color=color, nbins=nbins, marginal=marginal, title=title)
    return get_figure_output(fig, format=format)

async def plot_box(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str:
    """Create a box plot. points: 'all', 'outliers', 'suspectedoutliers', False."""
    df = parse_data_frame(data)
    fig = px.box(df, x=x, y=y, color=color, points=points, title=title)
    return get_figure_output(fig, format=format)

async def plot_violin(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, box: bool = False, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str:
    """Create a violin plot."""
    df = parse_data_frame(data)
    fig = px.violin(df, x=x, y=y, color=color, box=box, points=points, title=title)
    return get_figure_output(fig, format=format)

async def plot_strip(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, stripmode: str = 'group', title: Optional[str] = None, format: str = 'png') -> str:
    """Create a strip plot (jitter). stripmode: 'group', 'overlay'."""
    df = parse_data_frame(data)
    fig = px.strip(df, x=x, y=y, color=color, stripmode=stripmode, title=title)
    return get_figure_output(fig, format=format)

async def plot_ecdf(data: DataInput, x: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str:
    """Create an ECDF plot."""
    df = parse_data_frame(data)
    fig = px.ecdf(df, x=x, color=color, markers=markers, title=title)
    return get_figure_output(fig, format=format)
