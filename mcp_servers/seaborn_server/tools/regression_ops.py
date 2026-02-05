from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput, VectorInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def lmplot(data: DataInput, x: str, y: str, hue: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, height: float = 5, aspect: float = 1) -> str:
    """Figure-level linear model plot."""
    df = parse_data_frame(data)
    g = sns.lmplot(
        data=df, x=x, y=y, hue=hue, col=col, row=row,
        height=height, aspect=aspect
    )
    return get_figure_as_base64(g)

async def regplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str:
    """Axes-level regression plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.regplot(data=df, x=x, y=y)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def residplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str:
    """Axes-level residuals plot."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.residplot(data=df, x=x, y=y)
    if title: ax.set_title(title)
    return get_figure_as_base64()
