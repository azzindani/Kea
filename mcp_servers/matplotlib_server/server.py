from mcp.server.fastmcp import FastMCP
from mcp_servers.matplotlib_server.tools import (
    basic_ops, stats_ops, scientific_ops, three_d_ops, 
    specialty_ops, layout_ops, animation_ops, patch_ops, 
    advanced_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("matplotlib_server", dependencies=["matplotlib", "pandas", "numpy", "seaborn", "scipy", "pillow"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Basic Plots
# ==========================================
@mcp.tool()
async def plot_line(x: VectorInput, y: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', linestyle: str = '-', marker: Optional[str] = None, label: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await basic_ops.plot_line(x, y, title, xlabel, ylabel, color, linestyle, marker, label, figsize)
@mcp.tool()
async def plot_scatter(x: VectorInput, y: VectorInput, s: Optional[VectorInput] = None, c: Optional[VectorInput] = None, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, alpha: float = 1.0, figsize: List[int] = [10, 6]) -> str: return await basic_ops.plot_scatter(x, y, s, c, title, xlabel, ylabel, alpha, figsize)
@mcp.tool()
async def plot_bar(x: VectorInput, height: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str: return await basic_ops.plot_bar(x, height, title, xlabel, ylabel, color, figsize)
@mcp.tool()
async def plot_pie(x: VectorInput, labels: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str: return await basic_ops.plot_pie(x, labels, title, figsize)
@mcp.tool()
async def plot_area(x: VectorInput, y: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await basic_ops.plot_area(x, y, labels, title, figsize)
@mcp.tool()
async def plot_step(x: VectorInput, y: VectorInput, where: str = 'pre', title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await basic_ops.plot_step(x, y, where, title, figsize)

# ==========================================
# 2. Statistical
# ==========================================
@mcp.tool()
async def plot_hist(x: VectorInput, bins: int = 10, title: Optional[str] = None, xlabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str: return await stats_ops.plot_hist(x, bins, title, xlabel, color, figsize)
@mcp.tool()
async def plot_boxplot(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await stats_ops.plot_boxplot(data, labels, title, figsize)
@mcp.tool()
async def plot_violin(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await stats_ops.plot_violin(data, labels, title, figsize)
@mcp.tool()
async def plot_errorbar(x: VectorInput, y: VectorInput, yerr: VectorInput, title: Optional[str] = None, fmt: str = '-o', figsize: List[int] = [10, 6]) -> str: return await stats_ops.plot_errorbar(x, y, yerr, title, fmt, figsize)
@mcp.tool()
async def plot_hexbin(x: VectorInput, y: VectorInput, gridsize: int = 50, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await stats_ops.plot_hexbin(x, y, gridsize, title, figsize)

# ==========================================
# 3. Scientific
# ==========================================
@mcp.tool()
async def plot_contour(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await scientific_ops.plot_contour(X, Y, Z, levels, title, figsize)
@mcp.tool()
async def plot_contourf(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await scientific_ops.plot_contourf(X, Y, Z, levels, title, figsize)
@mcp.tool()
async def plot_heatmap(data: DataInput, title: Optional[str] = None, cmap: str = 'viridis', figsize: List[int] = [10, 8]) -> str: return await scientific_ops.plot_heatmap(data, title, cmap, figsize)
@mcp.tool()
async def plot_stream(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await scientific_ops.plot_stream(X, Y, U, V, title, figsize)
@mcp.tool()
async def plot_quiver(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await scientific_ops.plot_quiver(X, Y, U, V, title, figsize)

# ==========================================
# 4. 3D & Specialty
# ==========================================
@mcp.tool()
async def plot_scatter3d(x: VectorInput, y: VectorInput, z: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await three_d_ops.plot_scatter3d(x, y, z, title, figsize)
@mcp.tool()
async def plot_surface(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await three_d_ops.plot_surface(X, Y, Z, title, figsize)
@mcp.tool()
async def plot_wireframe(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: return await three_d_ops.plot_wireframe(X, Y, Z, title, figsize)
@mcp.tool()
async def plot_polar(theta: VectorInput, r: VectorInput, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str: return await specialty_ops.plot_polar(theta, r, title, figsize)
@mcp.tool()
async def plot_stem(x: VectorInput, y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await specialty_ops.plot_stem(x, y, title, figsize)
@mcp.tool()
async def plot_stair(y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await specialty_ops.plot_stair(y, title, figsize)

# ==========================================
# 5. Layouts & Animation
# ==========================================
@mcp.tool()
async def create_mosaic(layout: str, plots: Dict[str, Dict[str, Any]], figsize: List[int] = [12, 8], title: Optional[str] = None) -> str: return await layout_ops.create_mosaic(layout, plots, figsize, title)
@mcp.tool()
async def create_animation(frames_data: List[DataInput], plot_type: str = 'line', x: Optional[DataInput] = None, title: Optional[str] = None, interval: int = 200, figsize: List[int] = [10, 6]) -> str: return await animation_ops.create_animation(frames_data, plot_type, x, title, interval, figsize)

# ==========================================
# 6. Advanced
# ==========================================
@mcp.tool()
async def draw_shapes(shapes: List[Dict[str, Any]], title: Optional[str] = None, x_lim: List[float] = [0, 10], y_lim: List[float] = [0, 10], figsize: List[int] = [10, 8]) -> str: return await patch_ops.draw_shapes(shapes, title, x_lim, y_lim, figsize)
@mcp.tool()
async def plot_sankey(flows: VectorInput, labels: Optional[VectorInput] = None, orientations: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await advanced_ops.plot_sankey(flows, labels, orientations, title, figsize)
@mcp.tool()
async def plot_table(data: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await advanced_ops.plot_table(data, title, figsize)
@mcp.tool()
async def plot_broken_barh(xranges: List[tuple], yrange: tuple, facecolors: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: return await advanced_ops.plot_broken_barh(xranges, yrange, facecolors, title, figsize)

# ==========================================
# 7. Super Tools
# ==========================================
@mcp.tool()
async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str: return await super_ops.create_dashboard(plots, layout, figsize)
@mcp.tool()
async def set_style(style: str) -> str: return await super_ops.set_style(style)
@mcp.tool()
async def get_styles() -> List[str]: return await super_ops.get_styles()

if __name__ == "__main__":
    mcp.run()
