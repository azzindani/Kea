from mcp_servers.matplotlib_server.tools.core_ops import parse_data_frame, parse_vector, setup_figure, get_figure_as_base64, DataInput, VectorInput
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def plot_hist(x: VectorInput, bins: int = 10, title: Optional[str] = None, xlabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str:
    """Create a histogram."""
    fig, ax = setup_figure(title, xlabel, "Frequency", tuple(figsize))
    x_vec = parse_vector(x)
    ax.hist(x_vec, bins=bins, color=color, alpha=0.7, edgecolor='black')
    return get_figure_as_base64(fig)

async def plot_boxplot(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a boxplot from multiple datasets."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    
    # data can be list of vectors or DataFrame
    df = parse_data_frame(data)
    # Convert df columns to list of arrays
    vals = [df[col].dropna().values for col in df.columns]
    if labels is None: labels = df.columns.tolist()
    
    ax.boxplot(vals, labels=labels)
    return get_figure_as_base64(fig)

async def plot_violin(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str:
    """Create a violin plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    df = parse_data_frame(data)
    vals = [df[col].dropna().values for col in df.columns]
    # Violinplot doesn't take labels arg directly in old versions, strict check?
    # Usually we construct positions or handle ticks manually
    parts = ax.violinplot(vals, showmeans=True)
    if labels:
        ax.set_xticks(np.arange(1, len(labels) + 1))
        ax.set_xticklabels(labels)
        
    return get_figure_as_base64(fig)

async def plot_errorbar(x: VectorInput, y: VectorInput, yerr: VectorInput, title: Optional[str] = None, fmt: str = '-o', figsize: List[int] = [10, 6]) -> str:
    """Create an errorbar plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    x_vec = parse_vector(x)
    y_vec = parse_vector(y)
    yerr_vec = parse_vector(yerr)
    ax.errorbar(x_vec, y_vec, yerr=yerr_vec, fmt=fmt, ecolor='red', capsize=5)
    return get_figure_as_base64(fig)

async def plot_hexbin(x: VectorInput, y: VectorInput, gridsize: int = 50, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str:
    """Create a hexbin plot."""
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    x_vec = parse_vector(x)
    y_vec = parse_vector(y)
    hb = ax.hexbin(x_vec, y_vec, gridsize=gridsize, cmap='inferno')
    fig.colorbar(hb, ax=ax)
    return get_figure_as_base64(fig)
