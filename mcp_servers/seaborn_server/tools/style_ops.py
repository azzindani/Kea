from mcp_servers.seaborn_server.tools.core_ops import setup_style
import seaborn as sns
from typing import Dict, Any, List, Optional, Union

async def set_theme(style: str = "darkgrid", palette: str = "deep", font_scale: float = 1.0) -> str:
    """Set the aesthetic style of the plots."""
    sns.set_theme(style=style, palette=palette, font_scale=font_scale)
    return f"Theme set to style='{style}', palette='{palette}'"

async def get_palette(palette: str = "deep", n_colors: int = 10, as_hex: bool = True) -> List[Any]:
    """Return a list of colors defining a color palette."""
    pal = sns.color_palette(palette, n_colors=n_colors, as_cmap=False)
    if as_hex:
        return pal.as_hex()
    return pal
