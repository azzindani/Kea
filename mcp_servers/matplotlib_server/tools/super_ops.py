from mcp_servers.matplotlib_server.tools.core_ops import get_figure_as_base64, parse_vector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str:
    """
    Create a dashboard grid of plots.
    'plots' is a list of dicts defining plot type and data.
    Keys: 'type', 'x', 'y', 'title'.
    Types: 'line', 'bar', 'scatter', 'hist'.
    """
    rows, cols = layout
    fig, axes = plt.subplots(rows, cols, figsize=tuple(figsize))
    axes_flat = axes.flatten()
    
    for i, plot_def in enumerate(plots):
        if i >= len(axes_flat): break
        ax = axes_flat[i]
        
        ptype = plot_def.get('type', 'line')
        x = parse_vector(plot_def.get('x'))
        y = parse_vector(plot_def.get('y'))
        title = plot_def.get('title')
        
        if title: ax.set_title(title)
        
        if ptype == 'line':
            ax.plot(x, y)
        elif ptype == 'bar':
            ax.bar(x, y)
        elif ptype == 'scatter':
            ax.scatter(x, y)
        elif ptype == 'hist':
            ax.hist(x)
            
    plt.tight_layout()
    return get_figure_as_base64(fig)

async def set_style(style: str) -> str:
    """Set the visual style (e.g., 'seaborn', 'ggplot', 'dark_background')."""
    try:
        plt.style.use(style)
        return f"Style set to {style}"
    except Exception as e:
        return f"Error setting style: {e}"

async def get_styles() -> List[str]:
    """Get list of available styles."""
    return plt.style.available
