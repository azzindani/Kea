
import sys
import os
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Clear MPLBACKEND before importing matplotlib (Kaggle sets invalid value)
os.environ.pop('MPLBACKEND', None)
import matplotlib
matplotlib.use("Agg")
from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
# from mcp_servers.matplotlib_server.tools import (
#     basic_ops, stats_ops, scientific_ops, three_d_ops, 
#     specialty_ops, layout_ops, animation_ops, patch_ops, 
#     advanced_ops, super_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

mcp = FastMCP("matplotlib_server", dependencies=["matplotlib", "pandas", "numpy", "seaborn", "scipy", "pillow"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Basic Plots
# ==========================================
@mcp.tool()
async def plot_line(x: VectorInput, y: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', linestyle: str = '-', marker: Optional[str] = None, label: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS line chart. [ACTION]
    
    [RAG Context]
    Standard line plot. Best for time series or continuous data.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_line(x, y, title, xlabel, ylabel, color, linestyle, marker, label, figsize)

@mcp.tool()
async def plot_scatter(x: VectorInput, y: VectorInput, s: Optional[VectorInput] = None, c: Optional[VectorInput] = None, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, alpha: float = 1.0, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS scatter chart. [ACTION]
    
    [RAG Context]
    Standard scatter plot. Best for correlation analysis.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_scatter(x, y, s, c, title, xlabel, ylabel, alpha, figsize)

@mcp.tool()
async def plot_bar(x: VectorInput, height: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str: 
    """PLOTS bar chart. [ACTION]
    
    [RAG Context]
    Standard bar chart. Best for categorical comparison.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_bar(x, height, title, xlabel, ylabel, color, figsize)

@mcp.tool()
async def plot_pie(x: VectorInput, labels: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str: 
    """PLOTS pie chart. [ACTION]
    
    [RAG Context]
    Standard pie chart. Best for part-to-whole comparison.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_pie(x, labels, title, figsize)

@mcp.tool()
async def plot_area(x: VectorInput, y: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS area chart. [ACTION]
    
    [RAG Context]
    Standard area chart. Best for stacked trends.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_area(x, y, labels, title, figsize)

@mcp.tool()
async def plot_step(x: VectorInput, y: VectorInput, where: str = 'pre', title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS step chart. [ACTION]
    
    [RAG Context]
    Standard step chart. Best for discrete changes.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_step(x, y, where, title, figsize)

# ==========================================
# 2. Statistical
# ==========================================
@mcp.tool()
async def plot_hist(x: VectorInput, bins: int = 10, title: Optional[str] = None, xlabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str: 
    """PLOTS histogram. [ACTION]
    
    [RAG Context]
    Standard histogram. Best for distribution analysis.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_hist(x, bins, title, xlabel, color, figsize)

@mcp.tool()
async def plot_boxplot(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS boxplot. [ACTION]
    
    [RAG Context]
    Standard boxplot. Best for statistical summary (quartiles, outliers).
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_boxplot(data, labels, title, figsize)

@mcp.tool()
async def plot_violin(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS violin plot. [ACTION]
    
    [RAG Context]
    Standard violin plot. Combines boxplot and KDE.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_violin(data, labels, title, figsize)

@mcp.tool()
async def plot_errorbar(x: VectorInput, y: VectorInput, yerr: VectorInput, title: Optional[str] = None, fmt: str = '-o', figsize: List[int] = [10, 6]) -> str: 
    """PLOTS error bars. [ACTION]
    
    [RAG Context]
    Standard error bar plot. Best for displaying uncertainty.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_errorbar(x, y, yerr, title, fmt, figsize)

@mcp.tool()
async def plot_hexbin(x: VectorInput, y: VectorInput, gridsize: int = 50, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS hexbin chart. [ACTION]
    
    [RAG Context]
    Standard hexbin plot. Best for dense scatter data.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_hexbin(x, y, gridsize, title, figsize)

# ==========================================
# 3. Scientific
# ==========================================
@mcp.tool()
async def plot_contour(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS contour chart. [ACTION]
    
    [RAG Context]
    Standard contour plot. Best for 3D surface representation in 2D.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_contour(X, Y, Z, levels, title, figsize)

@mcp.tool()
async def plot_contourf(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS filled contour. [ACTION]
    
    [RAG Context]
    Standard filled contour plot.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_contourf(X, Y, Z, levels, title, figsize)

@mcp.tool()
async def plot_heatmap(data: DataInput, title: Optional[str] = None, cmap: str = 'viridis', figsize: List[int] = [10, 8]) -> str: 
    """PLOTS heatmap. [ACTION]
    
    [RAG Context]
    Standard heatmap. Best for matrix visualization.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_heatmap(data, title, cmap, figsize)

@mcp.tool()
async def plot_stream(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS stream plot. [ACTION]
    
    [RAG Context]
    Standard stream plot. Best for vector fields.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_stream(X, Y, U, V, title, figsize)

@mcp.tool()
async def plot_quiver(X: DataInput, Y: DataInput, U: DataInput, V: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS quiver plot. [ACTION]
    
    [RAG Context]
    Standard quiver plot. Best for vector fields with arrows.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_quiver(X, Y, U, V, title, figsize)

# ==========================================
# 4. 3D & Specialty
# ==========================================
@mcp.tool()
async def plot_scatter3d(x: VectorInput, y: VectorInput, z: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS 3D scatter. [ACTION]
    
    [RAG Context]
    3D scatter plot. Best for 3-variable correlation.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import three_d_ops
    return await three_d_ops.plot_scatter3d(x, y, z, title, figsize)

@mcp.tool()
async def plot_surface(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS 3D surface. [ACTION]
    
    [RAG Context]
    3D surface plot. Best for smooth 3-variable data.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import three_d_ops
    return await three_d_ops.plot_surface(X, Y, Z, title, figsize)

@mcp.tool()
async def plot_wireframe(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS 3D wireframe. [ACTION]
    
    [RAG Context]
    3D wireframe plot. Faster than surface plot.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import three_d_ops
    return await three_d_ops.plot_wireframe(X, Y, Z, title, figsize)

@mcp.tool()
async def plot_polar(theta: VectorInput, r: VectorInput, title: Optional[str] = None, figsize: List[int] = [8, 8]) -> str: 
    """PLOTS polar chart. [ACTION]
    
    [RAG Context]
    Polar plot. Best for cyclical or directional data.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import specialty_ops
    return await specialty_ops.plot_polar(theta, r, title, figsize)

@mcp.tool()
async def plot_stem(x: VectorInput, y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS stem chart. [ACTION]
    
    [RAG Context]
    Stem plot. Best for discrete data points.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import specialty_ops
    return await specialty_ops.plot_stem(x, y, title, figsize)

@mcp.tool()
async def plot_stair(y: VectorInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS stair chart. [ACTION]
    
    [RAG Context]
    Stair plot. Best for step-function data.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import specialty_ops
    return await specialty_ops.plot_stair(y, title, figsize)

# ==========================================
# 5. Layouts & Animation
# ==========================================
@mcp.tool()
async def create_mosaic(layout: str, plots: Dict[str, Dict[str, Any]], figsize: List[int] = [12, 8], title: Optional[str] = None) -> str: 
    """CREATES mosaic layout. [ACTION]
    
    [RAG Context]
    Complex subplot layout.
    Args:
        layout: Semantic layout string (e.g. "AAB;CCD").
    """
    from mcp_servers.matplotlib_server.tools import layout_ops
    return await layout_ops.create_mosaic(layout, plots, figsize, title)

@mcp.tool()
async def create_animation(frames_data: List[DataInput], plot_type: str = 'line', x: Optional[DataInput] = None, title: Optional[str] = None, interval: int = 200, figsize: List[int] = [10, 6]) -> str: 
    """CREATES animation. [ACTION]
    
    [RAG Context]
    Generates GIF/MP4 animation from frames.
    Returns path to video file.
    """
    from mcp_servers.matplotlib_server.tools import animation_ops
    return await animation_ops.create_animation(frames_data, plot_type, x, title, interval, figsize)

# ==========================================
# 6. Advanced
# ==========================================
@mcp.tool()
async def draw_shapes(shapes: List[Dict[str, Any]], title: Optional[str] = None, x_lim: List[float] = [0, 10], y_lim: List[float] = [0, 10], figsize: List[int] = [10, 8]) -> str: 
    """DRAWS shapes. [ACTION]
    
    [RAG Context]
    Draws custom shapes (rectangles, circles, polygons).
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import patch_ops
    return await patch_ops.draw_shapes(shapes, title, x_lim, y_lim, figsize)

@mcp.tool()
async def plot_sankey(flows: VectorInput, labels: Optional[VectorInput] = None, orientations: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS Sankey diagram. [ACTION]
    
    [RAG Context]
    Sankey diagram for flow visualization.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import advanced_ops
    return await advanced_ops.plot_sankey(flows, labels, orientations, title, figsize)

@mcp.tool()
async def plot_table(data: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS table. [ACTION]
    
    [RAG Context]
    Renders data frame as a static table image.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import advanced_ops
    return await advanced_ops.plot_table(data, title, figsize)

@mcp.tool()
async def plot_broken_barh(xranges: List[tuple], yrange: tuple, facecolors: Optional[VectorInput] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """PLOTS broken barh. [ACTION]
    
    [RAG Context]
    Broken horizontal bar plot. Best for Gantt charts or intervals.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import advanced_ops
    return await advanced_ops.plot_broken_barh(xranges, yrange, facecolors, title, figsize)

# ==========================================
# 7. Super Tools
# ==========================================
@mcp.tool()
async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str: 
    """CREATES dashboard. [ACTION]
    
    [RAG Context]
    Combines multiple plots into a single dashboard image.
    Returns path to saved image.
    """
    from mcp_servers.matplotlib_server.tools import super_ops
    return await super_ops.create_dashboard(plots, layout, figsize)

@mcp.tool()
async def set_style(style: str) -> str: 
    """SETS plot style. [ACTION]
    
    [RAG Context]
    Sets global matplotlib style (e.g. 'seaborn', 'ggplot').
    """
    from mcp_servers.matplotlib_server.tools import super_ops
    return await super_ops.set_style(style)

@mcp.tool()
async def get_styles() -> List[str]: 
    """GETS available styles. [DATA]
    
    [RAG Context]
    Returns list of valid style names.
    """
    from mcp_servers.matplotlib_server.tools import super_ops
    return await super_ops.get_styles()

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class MatplotlibServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
