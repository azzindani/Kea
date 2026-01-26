from mcp_servers.matplotlib_server.tools.core_ops import parse_data_frame, parse_vector, setup_figure, get_figure_as_base64, DataInput, VectorInput
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def plot_line(x: VectorInput, y: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', linestyle: str = '-', marker: Optional[str] = None, label: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a line plot."""
    fig, ax = setup_figure(title, xlabel, ylabel, tuple(figsize))
    x_vec = parse_vector(x)
    y_vec = parse_vector(y)
    ax.plot(x_vec, y_vec, color=color, linestyle=linestyle, marker=marker, label=label)
    if label: ax.legend()
    return get_figure_as_base64(fig)

async def plot_scatter(x: VectorInput, y: VectorInput, s: Optional[VectorInput] = None, c: Optional[VectorInput] = None, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, alpha: float = 1.0, figsize: List[int] = [10, 6]) -> str:
    """Create a scatter plot."""
    fig, ax = setup_figure(title, xlabel, ylabel, tuple(figsize))
    x_vec = parse_vector(x)
    y_vec = parse_vector(y)
    s_vec = parse_vector(s) if s is not None else None
    c_vec = parse_vector(c) if c is not None else None
    
    sc = ax.scatter(x_vec, y_vec, s=s_vec, c=c_vec, alpha=alpha)
    if c is not None: fig.colorbar(sc, ax=ax)
    return get_figure_as_base64(fig)

async def plot_bar(x: VectorInput, height: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str:
    """Create a bar chart."""
    fig, ax = setup_figure(title, xlabel, ylabel, tuple(figsize))
    x_vec = parse_vector(x)
    h_vec = parse_vector(height)
    ax.bar(x_vec, h_vec, color=color)
    return get_figure_as_base64(fig)

async def plot_pie(x: VectorInput, labels: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str:
    """Create a pie chart."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    x_vec = parse_vector(x)
    l_vec = parse_vector(labels) if labels is not None else None
    ax.pie(x_vec, labels=l_vec, autopct='%1.1f%%')
    return get_figure_as_base64(fig)

async def plot_area(x: VectorInput, y: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a stackplot (area plot)."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    x_vec = parse_vector(x)
    
    # Needs handling of list of lists for y or DataFrame
    from mcp_servers.matplotlib_server.tools.core_ops import parse_data_frame
    if isinstance(y, (list, str)):
        # Assume it describes multiple series
        # If string/basic list, try parsing as DF
        try:
             y_df = parse_data_frame(y)
             ys = [y_df[col].values for col in y_df.columns]
             if labels is None: labels = y_df.columns.tolist()
        except:
             # Just one series?
             ys = [parse_vector(y)]
    else:
        ys = [parse_vector(y)]
        
    ax.stackplot(x_vec, *ys, labels=labels)
    if labels: ax.legend(loc='upper left')
    return get_figure_as_base64(fig)

async def plot_step(x: VectorInput, y: VectorInput, where: str = 'pre', title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a step plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    x_vec = parse_vector(x)
    y_vec = parse_vector(y)
    ax.step(x_vec, y_vec, where=where)
    return get_figure_as_base64(fig)
