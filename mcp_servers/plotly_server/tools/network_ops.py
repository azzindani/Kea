from mcp_servers.plotly_server.tools.core_ops import get_figure_output
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union

async def plot_sankey(labels: List[str], source: List[int], target: List[int], value: List[float], title: Optional[str] = None, format: str = 'png') -> str:
    """Create a Sankey diagram."""
    fig = go.Figure(data=[go.Sankey(
        node=dict(label=labels),
        link=dict(source=source, target=target, value=value)
    )])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_table(header: List[str], cells: List[List[Any]], title: Optional[str] = None, format: str = 'png') -> str:
    """Render data as a table figure."""
    fig = go.Figure(data=[go.Table(
        header=dict(values=header),
        cells=dict(values=cells)
    )])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)
