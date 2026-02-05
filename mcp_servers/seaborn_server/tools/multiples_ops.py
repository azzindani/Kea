from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Union

async def pairplot(data: DataInput, hue: Optional[str] = None, kind: str = 'scatter', diag_kind: str = 'auto') -> str:
    """Plot pairwise relationships in a dataset."""
    df = parse_data_frame(data)
    g = sns.pairplot(data=df, hue=hue, kind=kind, diag_kind=diag_kind)
    return get_figure_as_base64(g)

async def jointplot(data: DataInput, x: str, y: str, kind: str = 'scatter', hue: Optional[str] = None) -> str:
    """Draw a plot of two variables with bivariate and univariate graphs."""
    df = parse_data_frame(data)
    g = sns.jointplot(data=df, x=x, y=y, kind=kind, hue=hue)
    return get_figure_as_base64(g)
