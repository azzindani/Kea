from mcp_servers.matplotlib_server.tools.core_ops import parse_data_frame, parse_vector, setup_figure, get_figure_as_base64, DataInput, VectorInput
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def plot_contour(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a contour plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    # Assuming X, Y, Z come as grids or lists of lists
    # Need robust parsing for Scientific grids (usually arrays)
    # Just parse as DF then values?
    # Usually X, Y, Z are 2D arrays. DataInput -> DF -> values
    
    # Simplified parsing: Assume nested lists for Z, X/Y can be ranges or grids
    # If Z is parsed from json, it's list of lists
    
    if isinstance(Z, str):
        # Allow passing just numpy-like string
        import json
        try:
            Z_arr = np.array(json.loads(Z))
        except:
            # Fallback
            pass
    else:
        Z_arr = np.array(Z) if isinstance(Z, list) else parse_data_frame(Z).values
        
    if X is not None:
        X_arr = np.array(X) if isinstance(X, list) else parse_data_frame(X).values
    else:
        X_arr = np.arange(Z_arr.shape[1])
        
    if Y is not None:
        Y_arr = np.array(Y) if isinstance(Y, list) else parse_data_frame(Y).values
    else:
        Y_arr = np.arange(Z_arr.shape[0])

    cs = ax.contour(X_arr, Y_arr, Z_arr, levels=levels)
    ax.clabel(cs, inline=True, fontsize=10)
    return get_figure_as_base64(fig)

async def plot_contourf(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a filled contour plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    # Logic similar to contour
    import json
    Z_arr = np.array(Z) if isinstance(Z, list) else parse_data_frame(Z).values
    # X, Y handling same as above (simplified here)
    X_arr = np.arange(Z_arr.shape[1])
    Y_arr = np.arange(Z_arr.shape[0])
    
    cf = ax.contourf(X_arr, Y_arr, Z_arr, levels=levels)
    fig.colorbar(cf, ax=ax)
    return get_figure_as_base64(fig)

async def plot_heatmap(data: DataInput, title: Optional[str] = None, cmap: str = 'viridis', figsize: List[int] = [10, 8]) -> str:
    """Create a heatmap (imshow)."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    df = parse_data_frame(data)
    matrix = df.values
    
    im = ax.imshow(matrix, cmap=cmap, aspect='auto')
    fig.colorbar(im, ax=ax)
    
    # Tick labels?
    ax.set_xticks(np.arange(len(df.columns)))
    ax.set_yticks(np.arange(len(df)))
    ax.set_xticklabels(df.columns)
    # Y labels might be default indices
    
    return get_figure_as_base64(fig)

async def plot_stream(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a streamplot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    # Assume 1D X, Y and 2D U, V
    X_arr = parse_vector(X).values
    Y_arr = parse_vector(Y).values
    
    # Grid construction needed for streamplot
    # Or assume X, Y are 1D arrays defining grid
    
    # Handle U, V as DFs or Lists of Lists
    U_arr = np.array(U) if isinstance(U, list) else parse_data_frame(U).values
    V_arr = np.array(V) if isinstance(V, list) else parse_data_frame(V).values
    
    ax.streamplot(X_arr, Y_arr, U_arr, V_arr)
    return get_figure_as_base64(fig)

async def plot_quiver(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a quiver plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    # Assume same as streamplot, but X, Y might be 2D
    X_arr = np.array(X)
    Y_arr = np.array(Y)
    U_arr = np.array(U)
    V_arr = np.array(V)
    
    ax.quiver(X_arr, Y_arr, U_arr, V_arr)
    return get_figure_as_base64(fig)
