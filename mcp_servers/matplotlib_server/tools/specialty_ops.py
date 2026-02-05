from mcp_servers.matplotlib_server.tools.core_ops import parse_vector, get_figure_as_base64, VectorInput
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def plot_polar(theta: VectorInput, r: VectorInput, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str:
    """Create a polar plot."""
    fig = plt.figure(figsize=tuple(figsize))
    ax = fig.add_subplot(111, projection='polar')
    if title: ax.set_title(title)
    
    ax.plot(parse_vector(theta), parse_vector(r))
    return get_figure_as_base64(fig)

async def plot_stem(x: VectorInput, y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a stem plot."""
    fig, ax = plt.figure(figsize=tuple(figsize)), plt.gca()
    if title: ax.set_title(title)
    
    ax.stem(parse_vector(x), parse_vector(y))
    return get_figure_as_base64(fig)

async def plot_stair(y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a stair plot."""
    fig, ax = plt.figure(figsize=tuple(figsize)), plt.gca()
    if title: ax.set_title(title)
    
    ax.stairs(parse_vector(y))
    return get_figure_as_base64(fig)
