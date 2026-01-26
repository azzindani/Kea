from mcp.server.fastmcp import FastMCP
from mcp_servers.seaborn_server.tools import (
    relational_ops, distribution_ops, categorical_ops, 
    regression_ops, matrix_ops, multiples_ops, 
    style_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("seaborn_server", dependencies=["seaborn", "matplotlib", "pandas", "numpy", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Relational
# ==========================================
@mcp.tool()
async def relplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, kind: str = 'scatter', height: float = 5, aspect: float = 1) -> str: return await relational_ops.relplot(data, x, y, hue, style, size, col, row, kind, height, aspect)
@mcp.tool()
async def scatterplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: return await relational_ops.scatterplot(data, x, y, hue, style, size, title)
@mcp.tool()
async def lineplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: return await relational_ops.lineplot(data, x, y, hue, style, size, title)

# ==========================================
# 2. Distribution
# ==========================================
@mcp.tool()
async def displot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'hist', height: float = 5, aspect: float = 1) -> str: return await distribution_ops.displot(data, x, y, hue, row, col, kind, height, aspect)
@mcp.tool()
async def histplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, bins: Union[int, str] = 'auto', kde: bool = False, title: Optional[str] = None) -> str: return await distribution_ops.histplot(data, x, y, hue, bins, kde, title)
@mcp.tool()
async def kdeplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, fill: bool = False, title: Optional[str] = None) -> str: return await distribution_ops.kdeplot(data, x, y, hue, fill, title)
@mcp.tool()
async def ecdfplot(data: DataInput, x: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: return await distribution_ops.ecdfplot(data, x, hue, title)
@mcp.tool()
async def rugplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, height: float = 0.05) -> str: return await distribution_ops.rugplot(data, x, y, hue, height)

# ==========================================
# 3. Categorical
# ==========================================
@mcp.tool()
async def catplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'strip', height: float = 5, aspect: float = 1) -> str: return await categorical_ops.catplot(data, x, y, hue, row, col, kind, height, aspect)
@mcp.tool()
async def boxplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: return await categorical_ops.boxplot(data, x, y, hue, title)
@mcp.tool()
async def violinplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, split: bool = False, title: Optional[str] = None) -> str: return await categorical_ops.violinplot(data, x, y, hue, split, title)
@mcp.tool()
async def barplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: return await categorical_ops.barplot(data, x, y, hue, title)
@mcp.tool()
async def countplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: return await categorical_ops.countplot(data, x, y, hue, title)

# ==========================================
# 4. Regression
# ==========================================
@mcp.tool()
async def lmplot(data: DataInput, x: str, y: str, hue: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, height: float = 5, aspect: float = 1) -> str: return await regression_ops.lmplot(data, x, y, hue, col, row, height, aspect)
@mcp.tool()
async def regplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: return await regression_ops.regplot(data, x, y, title)
@mcp.tool()
async def residplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: return await regression_ops.residplot(data, x, y, title)

# ==========================================
# 5. Matrix & Multiples
# ==========================================
@mcp.tool()
async def heatmap(data: DataInput, annot: bool = False, cmap: str = 'viridis', title: Optional[str] = None) -> str: return await matrix_ops.heatmap(data, annot, cmap, title)
@mcp.tool()
async def clustermap(data: DataInput, cmap: str = 'viridis', standard_scale: Optional[int] = None) -> str: return await matrix_ops.clustermap(data, cmap, standard_scale)
@mcp.tool()
async def pairplot(data: DataInput, hue: Optional[str] = None, kind: str = 'scatter', diag_kind: str = 'auto') -> str: return await multiples_ops.pairplot(data, hue, kind, diag_kind)
@mcp.tool()
async def jointplot(data: DataInput, x: str, y: str, kind: str = 'scatter', hue: Optional[str] = None) -> str: return await multiples_ops.jointplot(data, x, y, kind, hue)

# ==========================================
# 6. Style & Super
# ==========================================
@mcp.tool()
async def set_theme(style: str = "darkgrid", palette: str = "deep", font_scale: float = 1.0) -> str: return await style_ops.set_theme(style, palette, font_scale)
@mcp.tool()
async def get_palette(palette: str = "deep", n_colors: int = 10, as_hex: bool = True) -> List[Any]: return await style_ops.get_palette(palette, n_colors, as_hex)
@mcp.tool()
async def auto_plot(data: DataInput, x: str, y: Optional[str] = None) -> str: return await super_ops.auto_plot(data, x, y)
@mcp.tool()
async def create_dashboard(data: DataInput, plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str: return await super_ops.create_dashboard(data, plots, layout, figsize)

if __name__ == "__main__":
    mcp.run()
