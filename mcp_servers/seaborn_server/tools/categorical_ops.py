from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput, VectorInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def catplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'strip', height: float = 5, aspect: float = 1) -> str:
    """Figure-level categorical plot."""
    df = parse_data_frame(data)
    g = sns.catplot(
        data=df, x=x, y=y, hue=hue, row=row, col=col,
        kind=kind, height=height, aspect=aspect
    )
    return get_figure_as_base64(g)

async def boxplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level box plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.boxplot(data=df, x=x, y=y, hue=hue)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def violinplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, split: bool = False, title: Optional[str] = None) -> str:
    """Axes-level violin plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.violinplot(data=df, x=x, y=y, hue=hue, split=split)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def barplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level bar plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.barplot(data=df, x=x, y=y, hue=hue)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def countplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str:
    """Axes-level count plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.countplot(data=df, x=x, y=y, hue=hue)
    if title: ax.set_title(title)
    return get_figure_as_base64()
