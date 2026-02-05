from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def heatmap(data: DataInput, annot: bool = False, cmap: str = 'viridis', title: Optional[str] = None) -> str:
    """Plot rectangular data as a color-encoded matrix."""
    df = parse_data_frame(data)
    plt.figure()
    ax = sns.heatmap(data=df, annot=annot, cmap=cmap)
    if title: ax.set_title(title)
    return get_figure_as_base64()

async def clustermap(data: DataInput, cmap: str = 'viridis', standard_scale: Optional[int] = None) -> str:
    """Plot a matrix dataset as a hierarchically-clustered heatmap."""
    df = parse_data_frame(data)
    g = sns.clustermap(data=df, cmap=cmap, standard_scale=standard_scale)
    return get_figure_as_base64(g)
