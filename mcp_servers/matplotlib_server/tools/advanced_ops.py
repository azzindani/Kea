from mcp_servers.matplotlib_server.tools.core_ops import parse_vector, parse_data_frame, setup_figure, get_figure_as_base64, DataInput, VectorInput
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey
import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def plot_sankey(flows: VectorInput, labels: Optional[VectorInput] = None, orientations: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a Sankey diagram."""
    fig = plt.figure(figsize=tuple(figsize))
    ax = fig.add_subplot(1, 1, 1, xticks=[], yticks=[], title=title)
    
    flow_vec = parse_vector(flows)
    label_vec = parse_vector(labels).tolist() if labels is not None else None
    orient_vec = parse_vector(orientations).tolist() if orientations is not None else None
    
    sankey = Sankey(ax=ax, scale=0.01, offset=0.2, head_angle=180, format='%.0f', unit='')
    sankey.add(flows=flow_vec, labels=label_vec, orientations=orient_vec)
    sankey.finish()
    
    return get_figure_as_base64(fig)

async def plot_table(data: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Render a DataFrame as a table."""
    fig, ax = plt.subplots(figsize=tuple(figsize))
    ax.axis('tight')
    ax.axis('off')
    if title: ax.set_title(title)
    
    df = parse_data_frame(data)
    ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    
    return get_figure_as_base64(fig)

async def plot_broken_barh(xranges: List[tuple], yrange: tuple, facecolors: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a broken horizontal bar plot (Gantt-like)."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    
    # xranges should be list of (start, width) tuples
    # Expecting input like [(10, 30), (60, 20)]
    # If string/json, parse it.
    
    colors = parse_vector(facecolors).tolist() if facecolors is not None else 'tab:blue'
    
    ax.broken_barh(xranges, yrange, facecolors=colors)
    return get_figure_as_base64(fig)
