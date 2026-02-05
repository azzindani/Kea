from mcp_servers.matplotlib_server.tools.core_ops import parse_data_frame, parse_vector, get_figure_as_base64, DataInput, VectorInput
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional, Union
from mpl_toolkits.mplot3d import Axes3D # Init 3D

def setup_3d_figure(title=None, figsize=(10, 8)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    if title: ax.set_title(title)
    return fig, ax

async def plot_scatter3d(x: VectorInput, y: VectorInput, z: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a 3D scatter plot."""
    fig, ax = setup_3d_figure(title, tuple(figsize))
    ax.scatter(parse_vector(x), parse_vector(y), parse_vector(z))
    return get_figure_as_base64(fig)

async def plot_surface(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a 3D surface plot."""
    fig, ax = setup_3d_figure(title, tuple(figsize))
    Z_arr = np.array(Z) if isinstance(Z, list) else parse_data_frame(Z).values
    # Meshgrid creation from 1D X/Y? Or assume passed as grids?
    # Simple assumption: X, Y are 2D grids same shape as Z
    X_arr = np.array(X)
    Y_arr = np.array(Y)
    
    ax.plot_surface(X_arr, Y_arr, Z_arr, cmap='viridis')
    return get_figure_as_base64(fig)

async def plot_wireframe(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a 3D wireframe plot."""
    fig, ax = setup_3d_figure(title, tuple(figsize))
    X_arr = np.array(X)
    Y_arr = np.array(Y)
    Z_arr = np.array(Z)
    ax.plot_wireframe(X_arr, Y_arr, Z_arr)
    return get_figure_as_base64(fig)
