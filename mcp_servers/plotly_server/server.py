
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "kaleido",
#   "mcp",
#   "numpy",
#   "pandas",
#   "plotly",
#   "scipy",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    basic_ops, distribution_ops, finance_ops, 
    map_ops, hierarchical_ops, three_d_ops, super_ops,
    animation_ops, parallel_ops, network_ops, polar_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("plotly_server", dependencies=["plotly", "kaleido", "pandas", "numpy", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]

# ==========================================
# 1. Basic
# ==========================================
@mcp.tool()
async def plot_scatter(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await basic_ops.plot_scatter(data, x, y, color, size, title, format)
@mcp.tool()
async def plot_line(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str: return await basic_ops.plot_line(data, x, y, color, markers, title, format)
@mcp.tool()
async def plot_bar(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, barmode: str = 'relative', title: Optional[str] = None, format: str = 'png') -> str: return await basic_ops.plot_bar(data, x, y, color, barmode, title, format)
@mcp.tool()
async def plot_pie(data: DataInput, names: str, values: str, hole: float = 0.0, title: Optional[str] = None, format: str = 'png') -> str: return await basic_ops.plot_pie(data, names, values, hole, title, format)

# ==========================================
# 2. Distribution
# ==========================================
@mcp.tool()
async def plot_histogram(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, nbins: Optional[int] = None, marginal: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await distribution_ops.plot_histogram(data, x, y, color, nbins, marginal, title, format)
@mcp.tool()
async def plot_box(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str: return await distribution_ops.plot_box(data, x, y, color, points, title, format)
@mcp.tool()
async def plot_violin(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, box: bool = False, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str: return await distribution_ops.plot_violin(data, x, y, color, box, points, title, format)
@mcp.tool()
async def plot_strip(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, stripmode: str = 'group', title: Optional[str] = None, format: str = 'png') -> str: return await distribution_ops.plot_strip(data, x, y, color, stripmode, title, format)
@mcp.tool()
async def plot_ecdf(data: DataInput, x: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str: return await distribution_ops.plot_ecdf(data, x, color, markers, title, format)

# ==========================================
# 3. Finance
# ==========================================
@mcp.tool()
async def plot_candlestick(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str: return await finance_ops.plot_candlestick(data, x, open, high, low, close, title, format)
@mcp.tool()
async def plot_ohlc(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str: return await finance_ops.plot_ohlc(data, x, open, high, low, close, title, format)
@mcp.tool()
async def plot_waterfall(data: DataInput, x: str, y: str, measure: Optional[str] = None, text: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await finance_ops.plot_waterfall(data, x, y, measure, text, title, format)
@mcp.tool()
async def plot_funnel(data: DataInput, x: str, y: str, title: Optional[str] = None, format: str = 'png') -> str: return await finance_ops.plot_funnel(data, x, y, title, format)
@mcp.tool()
async def plot_indicator(value: float, delta_ref: Optional[float] = None, title: Optional[str] = None, mode: str = "number+delta", format: str = 'png') -> str: return await finance_ops.plot_indicator(value, delta_ref, title, mode, format)

# ==========================================
# 4. Maps
# ==========================================
@mcp.tool()
async def plot_scatter_map(data: DataInput, lat: str, lon: str, color: Optional[str] = None, size: Optional[str] = None, hover_name: Optional[str] = None, zoom: int = 3, title: Optional[str] = None, format: str = 'png') -> str: return await map_ops.plot_scatter_map(data, lat, lon, color, size, hover_name, zoom, title, format)
@mcp.tool()
async def plot_choropleth(data: DataInput, locations: str, color: str, locationmode: str = 'ISO-3', hover_name: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await map_ops.plot_choropleth(data, locations, color, locationmode, hover_name, title, format)
@mcp.tool()
async def plot_density_map(data: DataInput, lat: str, lon: str, z: Optional[str] = None, radius: int = 10, title: Optional[str] = None, format: str = 'png') -> str: return await map_ops.plot_density_map(data, lat, lon, z, radius, title, format)

# ==========================================
# 5. Hierarchical & 3D
# ==========================================
@mcp.tool()
async def plot_sunburst(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await hierarchical_ops.plot_sunburst(data, path, values, color, title, format)
@mcp.tool()
async def plot_treemap(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await hierarchical_ops.plot_treemap(data, path, values, color, title, format)
@mcp.tool()
async def plot_icicle(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await hierarchical_ops.plot_icicle(data, path, values, color, title, format)
@mcp.tool()
async def plot_scatter3d(data: DataInput, x: str, y: str, z: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await three_d_ops.plot_scatter3d(data, x, y, z, color, size, title, format)
@mcp.tool()
async def plot_surface(z: List[List[float]], x: Optional[List[Any]] = None, y: Optional[List[Any]] = None, title: Optional[str] = None, format: str = 'png') -> str: return await three_d_ops.plot_surface(z, x, y, title, format)
@mcp.tool()
async def plot_mesh3d(data: DataInput, x: str, y: str, z: str, alphahull: int = 0, title: Optional[str] = None, format: str = 'png') -> str: return await three_d_ops.plot_mesh3d(data, x, y, z, alphahull, title, format)

# ==========================================
# 6. Animation
# ==========================================
@mcp.tool()
async def plot_animated_scatter(data: DataInput, x: str, y: str, animation_frame: str, animation_group: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, range_x: Optional[List[float]] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str: return await animation_ops.plot_animated_scatter(data, x, y, animation_frame, animation_group, color, size, range_x, range_y, title, format)
@mcp.tool()
async def plot_animated_bar(data: DataInput, x: str, y: str, animation_frame: str, color: Optional[str] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str: return await animation_ops.plot_animated_bar(data, x, y, animation_frame, color, range_y, title, format)
@mcp.tool()
async def plot_animated_choropleth(data: DataInput, locations: str, color: str, animation_frame: str, locationmode: str = 'ISO-3', title: Optional[str] = None, format: str = 'png') -> str: return await animation_ops.plot_animated_choropleth(data, locations, color, animation_frame, locationmode, title, format)

# ==========================================
# 7. Parallel & Network
# ==========================================
@mcp.tool()
async def plot_parallel_coordinates(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await parallel_ops.plot_parallel_coordinates(data, dimensions, color, title, format)
@mcp.tool()
async def plot_parallel_categories(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await parallel_ops.plot_parallel_categories(data, dimensions, color, title, format)
@mcp.tool()
async def plot_sankey(labels: List[str], source: List[int], target: List[int], value: List[float], title: Optional[str] = None, format: str = 'png') -> str: return await network_ops.plot_sankey(labels, source, target, value, title, format)
@mcp.tool()
async def plot_table(header: List[str], cells: List[List[Any]], title: Optional[str] = None, format: str = 'png') -> str: return await network_ops.plot_table(header, cells, title, format)

# ==========================================
# 8. Polar
# ==========================================
@mcp.tool()
async def plot_scatter_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await polar_ops.plot_scatter_polar(data, r, theta, color, size, title, format)
@mcp.tool()
async def plot_line_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, line_close: bool = True, title: Optional[str] = None, format: str = 'png') -> str: return await polar_ops.plot_line_polar(data, r, theta, color, line_close, title, format)
@mcp.tool()
async def plot_bar_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: return await polar_ops.plot_bar_polar(data, r, theta, color, title, format)

# ==========================================
# 9. Super
# ==========================================
@mcp.tool()
async def auto_plot(data: DataInput, x: str, y: Optional[str] = None, color: Optional[str] = None, format: str = 'png') -> str: return await super_ops.auto_plot(data, x, y, color, format)
@mcp.tool()
async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], width: int = 1200, height: int = 800, format: str = 'png') -> str: return await super_ops.create_dashboard(plots, layout, width, height, format)

if __name__ == "__main__":
    mcp.run()