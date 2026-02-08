
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

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.plotly_server.tools import (
    basic_ops, distribution_ops, finance_ops, 
    map_ops, hierarchical_ops, three_d_ops, super_ops,
    animation_ops, parallel_ops, network_ops, polar_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("plotly_server", dependencies=["plotly", "kaleido", "pandas", "numpy", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]

# ==========================================
# 1. Basic
# ==========================================
@mcp.tool()
async def plot_scatter(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS scatter chart. [ACTION]
    
    [RAG Context]
    Interactive scatter plot.
    Returns path to saved image.
    """
    return await basic_ops.plot_scatter(data, x, y, color, size, title, format)

@mcp.tool()
async def plot_line(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS line chart. [ACTION]
    
    [RAG Context]
    Interactive line plot.
    Returns path to saved image.
    """
    return await basic_ops.plot_line(data, x, y, color, markers, title, format)

@mcp.tool()
async def plot_bar(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, barmode: str = 'relative', title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS bar chart. [ACTION]
    
    [RAG Context]
    Interactive bar chart.
    Returns path to saved image.
    """
    return await basic_ops.plot_bar(data, x, y, color, barmode, title, format)

@mcp.tool()
async def plot_pie(data: DataInput, names: str, values: str, hole: float = 0.0, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS pie chart. [ACTION]
    
    [RAG Context]
    Interactive pie chart.
    Returns path to saved image.
    """
    return await basic_ops.plot_pie(data, names, values, hole, title, format)

# ==========================================
# 2. Distribution
# ==========================================
@mcp.tool()
async def plot_histogram(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, nbins: Optional[int] = None, marginal: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS histogram. [ACTION]
    
    [RAG Context]
    Interactive histogram with marginals.
    Returns path to saved image.
    """
    return await distribution_ops.plot_histogram(data, x, y, color, nbins, marginal, title, format)

@mcp.tool()
async def plot_box(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS boxplot. [ACTION]
    
    [RAG Context]
    Interactive boxplot.
    Returns path to saved image.
    """
    return await distribution_ops.plot_box(data, x, y, color, points, title, format)

@mcp.tool()
async def plot_violin(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, box: bool = False, points: str = 'outliers', title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS violin plot. [ACTION]
    
    [RAG Context]
    Interactive violin plot.
    Returns path to saved image.
    """
    return await distribution_ops.plot_violin(data, x, y, color, box, points, title, format)

@mcp.tool()
async def plot_strip(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None, stripmode: str = 'group', title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS strip chart. [ACTION]
    
    [RAG Context]
    Interactive strip plot.
    Returns path to saved image.
    """
    return await distribution_ops.plot_strip(data, x, y, color, stripmode, title, format)

@mcp.tool()
async def plot_ecdf(data: DataInput, x: Optional[str] = None, color: Optional[str] = None, markers: bool = False, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS ECDF. [ACTION]
    
    [RAG Context]
    Interactive ECDF plot.
    Returns path to saved image.
    """
    return await distribution_ops.plot_ecdf(data, x, color, markers, title, format)

# ==========================================
# 3. Finance
# ==========================================
@mcp.tool()
async def plot_candlestick(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS candlestick. [ACTION]
    
    [RAG Context]
    Financial candlestick chart.
    Returns path to saved image.
    """
    return await finance_ops.plot_candlestick(data, x, open, high, low, close, title, format)

@mcp.tool()
async def plot_ohlc(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS OHLC. [ACTION]
    
    [RAG Context]
    Financial OHLC chart.
    Returns path to saved image.
    """
    return await finance_ops.plot_ohlc(data, x, open, high, low, close, title, format)

@mcp.tool()
async def plot_waterfall(data: DataInput, x: str, y: str, measure: Optional[str] = None, text: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS waterfall. [ACTION]
    
    [RAG Context]
    Financial waterfall chart.
    Returns path to saved image.
    """
    return await finance_ops.plot_waterfall(data, x, y, measure, text, title, format)

@mcp.tool()
async def plot_funnel(data: DataInput, x: str, y: str, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS funnel. [ACTION]
    
    [RAG Context]
    Funnel chart for conversion pipelines.
    Returns path to saved image.
    """
    return await finance_ops.plot_funnel(data, x, y, title, format)

@mcp.tool()
async def plot_indicator(value: float, delta_ref: Optional[float] = None, title: Optional[str] = None, mode: str = "number+delta", format: str = 'png') -> str: 
    """PLOTS indicator. [ACTION]
    
    [RAG Context]
    KPI gauge/indicator.
    Returns path to saved image.
    """
    return await finance_ops.plot_indicator(value, delta_ref, title, mode, format)

# ==========================================
# 4. Maps
# ==========================================
@mcp.tool()
async def plot_scatter_map(data: DataInput, lat: str, lon: str, color: Optional[str] = None, size: Optional[str] = None, hover_name: Optional[str] = None, zoom: int = 3, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS scatter map. [ACTION]
    
    [RAG Context]
    Scatter plot on a geographic map.
    Returns path to saved image.
    """
    return await map_ops.plot_scatter_map(data, lat, lon, color, size, hover_name, zoom, title, format)

@mcp.tool()
async def plot_choropleth(data: DataInput, locations: str, color: str, locationmode: str = 'ISO-3', hover_name: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS choropleth. [ACTION]
    
    [RAG Context]
    Geographic heat map (choropleth).
    Returns path to saved image.
    """
    return await map_ops.plot_choropleth(data, locations, color, locationmode, hover_name, title, format)

@mcp.tool()
async def plot_density_map(data: DataInput, lat: str, lon: str, z: Optional[str] = None, radius: int = 10, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS density map. [ACTION]
    
    [RAG Context]
    Geographic density heatmap.
    Returns path to saved image.
    """
    return await map_ops.plot_density_map(data, lat, lon, z, radius, title, format)

# ==========================================
# 5. Hierarchical & 3D
# ==========================================
@mcp.tool()
async def plot_sunburst(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS sunburst. [ACTION]
    
    [RAG Context]
    Hierarchical sunburst chart.
    Returns path to saved image.
    """
    return await hierarchical_ops.plot_sunburst(data, path, values, color, title, format)

@mcp.tool()
async def plot_treemap(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS treemap. [ACTION]
    
    [RAG Context]
    Hierarchical treemap chart.
    Returns path to saved image.
    """
    return await hierarchical_ops.plot_treemap(data, path, values, color, title, format)

@mcp.tool()
async def plot_icicle(data: DataInput, path: List[str], values: Optional[str] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS icicle. [ACTION]
    
    [RAG Context]
    Hierarchical icicle chart.
    Returns path to saved image.
    """
    return await hierarchical_ops.plot_icicle(data, path, values, color, title, format)

@mcp.tool()
async def plot_scatter3d(data: DataInput, x: str, y: str, z: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS 3D scatter. [ACTION]
    
    [RAG Context]
    Interactive 3D scatter plot.
    Returns path to saved image.
    """
    return await three_d_ops.plot_scatter3d(data, x, y, z, color, size, title, format)

@mcp.tool()
async def plot_surface(z: List[List[float]], x: Optional[List[Any]] = None, y: Optional[List[Any]] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS 3D surface. [ACTION]
    
    [RAG Context]
    Interactive 3D surface plot.
    Returns path to saved image.
    """
    return await three_d_ops.plot_surface(z, x, y, title, format)

@mcp.tool()
async def plot_mesh3d(data: DataInput, x: str, y: str, z: str, alphahull: int = 0, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS 3D mesh. [ACTION]
    
    [RAG Context]
    Interactive 3D molecular/mesh plot.
    Returns path to saved image.
    """
    return await three_d_ops.plot_mesh3d(data, x, y, z, alphahull, title, format)

# ==========================================
# 6. Animation
# ==========================================
@mcp.tool()
async def plot_animated_scatter(data: DataInput, x: str, y: str, animation_frame: str, animation_group: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, range_x: Optional[List[float]] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS animated scatter. [ACTION]
    
    [RAG Context]
    Scatter plot with time slider.
    Returns path to saved image.
    """
    return await animation_ops.plot_animated_scatter(data, x, y, animation_frame, animation_group, color, size, range_x, range_y, title, format)

@mcp.tool()
async def plot_animated_bar(data: DataInput, x: str, y: str, animation_frame: str, color: Optional[str] = None, range_y: Optional[List[float]] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS animated bar. [ACTION]
    
    [RAG Context]
    Bar chart with time slider.
    Returns path to saved image.
    """
    return await animation_ops.plot_animated_bar(data, x, y, animation_frame, color, range_y, title, format)

@mcp.tool()
async def plot_animated_choropleth(data: DataInput, locations: str, color: str, animation_frame: str, locationmode: str = 'ISO-3', title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS animated choropleth. [ACTION]
    
    [RAG Context]
    Map with time slider.
    Returns path to saved image.
    """
    return await animation_ops.plot_animated_choropleth(data, locations, color, animation_frame, locationmode, title, format)

# ==========================================
# 7. Parallel & Network
# ==========================================
# ==========================================
# 7. Parallel & Network
# ==========================================
@mcp.tool()
async def plot_parallel_coordinates(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS parallel coordinates. [ACTION]
    
    [RAG Context]
    Multivariate data visualization.
    Returns path to saved image.
    """
    return await parallel_ops.plot_parallel_coordinates(data, dimensions, color, title, format)

@mcp.tool()
async def plot_parallel_categories(data: DataInput, dimensions: Optional[List[str]] = None, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS parallel categories. [ACTION]
    
    [RAG Context]
    Multivariate categorical visualization.
    Returns path to saved image.
    """
    return await parallel_ops.plot_parallel_categories(data, dimensions, color, title, format)

@mcp.tool()
async def plot_sankey(labels: List[str], source: List[int], target: List[int], value: List[float], title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS Sankey chart. [ACTION]
    
    [RAG Context]
    Flow visualization (Sankey diagram).
    Returns path to saved image.
    """
    return await network_ops.plot_sankey(labels, source, target, value, title, format)

@mcp.tool()
async def plot_table(header: List[str], cells: List[List[Any]], title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS table. [ACTION]
    
    [RAG Context]
    Renders data as a static table image.
    Returns path to saved image.
    """
    return await network_ops.plot_table(header, cells, title, format)

# ==========================================
# 8. Polar
# ==========================================
@mcp.tool()
async def plot_scatter_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS polar scatter. [ACTION]
    
    [RAG Context]
    Polar coordinate scatter plot.
    Returns path to saved image.
    """
    return await polar_ops.plot_scatter_polar(data, r, theta, color, size, title, format)

@mcp.tool()
async def plot_line_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, line_close: bool = True, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS polar line. [ACTION]
    
    [RAG Context]
    Polar coordinate line plot (radar chart).
    Returns path to saved image.
    """
    return await polar_ops.plot_line_polar(data, r, theta, color, line_close, title, format)

@mcp.tool()
async def plot_bar_polar(data: DataInput, r: str, theta: str, color: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS polar bar. [ACTION]
    
    [RAG Context]
    Polar coordinate bar plot.
    Returns path to saved image.
    """
    return await polar_ops.plot_bar_polar(data, r, theta, color, title, format)

# ==========================================
# 9. Super
# ==========================================
@mcp.tool()
async def auto_plot(data: DataInput, x: str, y: Optional[str] = None, color: Optional[str] = None, format: str = 'png') -> str: 
    """PLOTS automatically. [ACTION]
    
    [RAG Context]
    Infers best plotly chart type from data.
    Returns path to saved image.
    """
    return await super_ops.auto_plot(data, x, y, color, format)

@mcp.tool()
async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], width: int = 1200, height: int = 800, format: str = 'png') -> str: 
    """CREATES dashboard. [ACTION]
    
    [RAG Context]
    Combines multiple plotly charts into a dashboard image.
    Returns path to saved image.
    """
    return await super_ops.create_dashboard(plots, layout, width, height, format)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PlotlyServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
