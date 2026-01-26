from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput, VectorInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def relplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, kind: str = 'scatter', height: float = 5, aspect: float = 1) -> str:
    """Figure-level relational plot (scatter or line)."""
    df = parse_data_frame(data)
    g = sns.relplot(
        data=df, x=x, y=y, hue=hue, style=style, size=size,
        col=col, row=row, kind=kind, height=height, aspect=aspect
    )
    return get_figure_as_base64(g)

async def scatterplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level scatter plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.scatterplot(data=df, x=x, y=y, hue=hue, style=style, size=size)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def lineplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level line plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.lineplot(data=df, x=x, y=y, hue=hue, style=style, size=size)
    if title: ax.set_title(title)
    return get_figure_as_base64()
