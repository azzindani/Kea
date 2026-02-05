from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union
import pandas as pd # Needed for Surface dict handling

async def plot_scatter3d(data: DataInput, x: str, y: str, z: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a 3D scatter plot."""
    df = parse_data_frame(data)
    fig = px.scatter_3d(df, x=x, y=y, z=z, color=color, size=size, title=title)
    return get_figure_output(fig, format=format)

async def plot_surface(z: List[List[float]], x: Optional[List[Any]] = None, y: Optional[List[Any]] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a 3D surface plot."""
    # Logic for surface usually expects 2D array (z)
    fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_mesh3d(data: DataInput, x: str, y: str, z: str, alphahull: int = 0, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a 3D mesh plot."""
    df = parse_data_frame(data)
    fig = go.Figure(data=[go.Mesh3d(x=df[x], y=df[y], z=df[z], alphahull=alphahull, opacity=0.5)])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)
