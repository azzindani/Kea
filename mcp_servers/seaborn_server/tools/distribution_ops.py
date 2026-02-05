from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput, VectorInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def displot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'hist', height: float = 5, aspect: float = 1) -> str:
    """Figure-level distribution plot."""
    df = parse_data_frame(data)
    g = sns.displot(
        data=df, x=x, y=y, hue=hue, row=row, col=col, 
        kind=kind, height=height, aspect=aspect
    )
    return get_figure_as_base64(g)

async def histplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, bins: Union[int, str] = 'auto', kde: bool = False, title: Optional[str] = None) -> str:
    """Axes-level histogram."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.histplot(data=df, x=x, y=y, hue=hue, bins=bins, kde=kde)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def kdeplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, fill: bool = False, title: Optional[str] = None) -> str:
    """Axes-level Kernel Density Estimate."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.kdeplot(data=df, x=x, y=y, hue=hue, fill=fill)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def ecdfplot(data: DataInput, x: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level Empirical Cumulative Distribution Function."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.ecdfplot(data=df, x=x, hue=hue)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def rugplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, height: float = 0.05) -> str:
    """Axes-level rug plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.rugplot(data=df, x=x, y=y, hue=hue, height=height)
    return get_figure_as_base64()
