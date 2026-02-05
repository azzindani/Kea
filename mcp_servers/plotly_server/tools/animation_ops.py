from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_animated_scatter(data: DataInput, x: str, y: str, animation_frame: str, animation_group: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, range_x: Optional[List[float]] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create an animated scatter plot."""
    df = parse_data_frame(data)
    fig = px.scatter(df, x=x, y=y, animation_frame=animation_frame, animation_group=animation_group, color=color, size=size, range_x=range_x, range_y=range_y, title=title)
    return get_figure_output(fig, format=format)

async def plot_animated_bar(data: DataInput, x: str, y: str, animation_frame: str, color: Optional[str] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create an animated bar chart."""
    df = parse_data_frame(data)
    fig = px.bar(df, x=x, y=y, animation_frame=animation_frame, color=color, range_y=range_y, title=title)
    return get_figure_output(fig, format=format)

async def plot_animated_choropleth(data: DataInput, locations: str, color: str, animation_frame: str, locationmode: str = 'ISO-3', title: Optional[str] = None, format: str = 'png') -> str:
    """Create an animated choropleth map."""
    df = parse_data_frame(data)
    fig = px.choropleth(df, locations=locations, color=color, animation_frame=animation_frame, locationmode=locationmode, title=title)
    return get_figure_output(fig, format=format)
