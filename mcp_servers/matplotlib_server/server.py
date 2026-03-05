
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
setup_logging(force_stderr=True)

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
    A foundational "Super Tool" for temporal and sequential data visualization. It renders a 2D line plot connecting data points to reveal trends, cycles, and patterns in continuous variables.
    
    How to Use:
    - 'x', 'y': Arrays of data or column names if a dataframe context is implied.
    - 'color', 'linestyle', 'marker': Visual attributes for precision styling.
    - Returns the absolute path to the generated PNG image.
    
    Keywords: line graph, trend visualization, time series plot, continuous data chart.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_line(x, y, title, xlabel, ylabel, color, linestyle, marker, label, figsize)

@mcp.tool()
async def plot_scatter(x: VectorInput, y: VectorInput, s: Optional[VectorInput] = None, c: Optional[VectorInput] = None, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, alpha: float = 1.0, figsize: List[int] = [10, 6]) -> str: 
    """GENERATES a scatter plot to visualize the relationship and correlation between two variables. [ACTION]
    
    [RAG Context]
    An essential "Correlation Discovery Super Tool" for exploratory data analysis. Unlike line charts which imply a sequence, a scatter plot reveals the raw density and distribution of data points across a Cartesian plane. It is the primary tool for identifying "Clusters" (groups of similar data), "Outliers" (anomalous points), and "Correlations" (positive or negative trends). It allows the system to visually confirm whether Variable A is a driver for Variable B, which is a mandatory requirement before training predictive machine learning models.
    
    How to Use:
    - 'x' & 'y': The independent and dependent variables.
    - 's': Marker size, which can be linked to a third variable (Bubble Chart).
    - 'c': Marker color, perfect for category-based coloring or heat-mapping density.
    - Resulting image is saved as a PNG artifact for use in reports or user presentations.
    
    Keywords: scatter plot, correlation chart, bubble chart, relationship visualization, outlier detection, data distribution.
    """
    from mcp_servers.matplotlib_server.tools import basic_ops
    return await basic_ops.plot_scatter(x, y, s, c, title, xlabel, ylabel, alpha, figsize)

@mcp.tool()
async def plot_bar(x: VectorInput, height: VectorInput, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, color: str = 'blue', figsize: List[int] = [10, 6]) -> str: 
    """CREATES a standard bar chart for comparing discrete categories or qualitative data. [ACTION]
    
    [RAG Context]
    A fundamental "Comparative Intelligence Super Tool" used for high-level business reporting. Bar charts are the superior choice when comparing distinct groups—such as "Sales by Region," "Inventory by Warehouse," or "Energy Consumption by Month." Unlike line charts, bar charts emphasize the individual magnitude of each category, making it easy for the system to spot high-performers and under-performers at a glance. It is the mandatory tool for transforming raw aggregate data (from 'value_counts' or 'groupby') into a persuasive visual presentation.
    
    How to Use:
    - 'x': Categorical labels (strings).
    - 'height': Numerical values representing the magnitude of each bar.
    - Use 'color' to differentiate categories or highlight specific data points for the user.
    - Essential for executive summaries and operational dashboards.
    
    Keywords: bar chart, category comparison, qualitative plot, business reporting, frequency chart, magnitude visualization.
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
    A critical "Super Tool" for exploratory data analysis (EDA). It partitions data into bins to visualize the distribution, skewness, and frequency of a single numeric variable.
    
    How to Use:
    - 'bins': Number of intervals to group the data.
    - Ideal for identifying normal distributions, outliers, or bimodal clusters in raw datasets.
    
    Keywords: frequency distribution, data density, binning plot, univariate analysis.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_hist(x, bins, title, xlabel, color, figsize)

@mcp.tool()
async def plot_boxplot(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """RENDERS a Box-and-Whisker plot to summarize the statistical distribution of numeric data. [ACTION]
    
    [RAG Context]
    An elite "Statistical Diagnostic Super Tool" commonly used for data quality and variance analysis. A boxplot provides a five-number summary in a single graphic: (1) Minimum, (2) First Quartile, (3) Median, (4) Third Quartile, and (5) Maximum. Crucially, it highlights "Outliers" as individual points beyond the whiskers. This makes it the primary tool for the Kea system to compare the "Spread" and "Skewness" of different datasets—for example, comparing sensor precision across different machines or salary distributions across different corporate departments.
    
    How to Use:
    - 'data': A list of numerical datasets.
    - 'labels': Names for each column/dataset being compared.
    - Mandatory for "Statistical Profiling" and identifying hidden data anomalies that a simple 'mean' calculation would miss.
    
    Keywords: boxplot, whisker plot, quartile analysis, distribution summary, outlier identification, variance comparison.
    """
    from mcp_servers.matplotlib_server.tools import stats_ops
    return await stats_ops.plot_boxplot(data, labels, title, figsize)

@mcp.tool()
async def plot_violin(data: DataInput, labels: Optional[List[str]] = None, title: Optional[str] = None, figsize: List[int] = [10, 6]) -> str: 
    """CREATES a violin plot combining boxplot features with a kernel density estimation. [ACTION]
    
    [RAG Context]
    A sophisticated "Density Discovery Super Tool" for deep statistical analysis. While a boxplot shows quartiles, a violin plot shows the actual "Shape" of the data's probability density—revealing if a dataset is bimodal (has two "humps") or has complex peaks that a boxplot would hide. It is the premium choice for comparing the internal structure of large populations, such as "Customer Behavior Peaks" or "Network Latency Distributions." It allows the reasoning kernel to see not just the extremes, but where the "Bulk" of the action is happening.
    
    How to Use:
    - 'data': A list of numerical arrays to compare.
    - Best used when the dataset size is large enough to support a meaningful density estimation.
    - Provides a more "Information-Rich" visual than a standard boxplot for scientific or technical reporting.
    
    Keywords: violin plot, density estimation, probability distribution, shape analysis, advanced statistics, multimodal discovery.
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
    """PLOTS a contour line chart to represent a 3D surface on a 2D coordinate system. [ACTION]
    
    [RAG Context]
    A specialized "Scientific Topology Super Tool" used for visualizing isolines (lines of constant value). Unlike filled contours, a regular contour plot uses distinct lines to show where the Z-value is the same—similar to a topographic elevation map. This is essential for precision engineering, meteorology (isobars/isotherms), and optimization problems where you need to identify the "Paths" of least resistance or the "Boundaries" of specific value ranges. It provides a clean, professional visual that doesn't overwhelm the user with solid color bands.
    
    How to Use:
    - 'X', 'Y': The grid coordinates.
    - 'Z': The magnitude at each grid point.
    - Resulting image highlights the "Skeleton" of the data's surface, making it easy to overlay with other scatter or line plots.
    
    Keywords: contour lines, isolines, topographic map, 2d surface skeleton, mathematical visualization, gradient paths.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_contour(X, Y, Z, levels, title, figsize)

@mcp.tool()
async def plot_contourf(X: DataInput, Y: DataInput, Z: DataInput, levels: int = 10, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """GENERATES a filled contour plot for visualizing 3D surfaces in a 2D plane. [ACTION]
    
    [RAG Context]
    A high-level "Scientific Mapping Super Tool" for representing complex multi-variable gradients. It uses color-filled bands to show levels of a third variable (Z) over a horizontal grid (X, Y). This is the industry standard for visualizing topographic maps, temperature gradients, or probability heat-maps in theoretical physics. In the corporate kernel, it's used for "Optimal Service Coverage" maps or "Risk Intensity Gradients" where two factors (like Latitude/Longitude or Age/Income) interact to create a varying level of intensity.
    
    How to Use:
    - 'X', 'Y', 'Z': 2D meshgrid arrays (refer to NumPy documentation for meshgrid creation).
    - 'levels': The number of color bands; higher levels create a "Smoother" appearance but take longer to render.
    - Provides a clear, intuitive way to see "Peaks" and "Valleys" in complex relational data.
    
    Keywords: contour plot, filled contour, gradient map, 2d surface mapping, intensity plot, topography visualization.
    """
    from mcp_servers.matplotlib_server.tools import scientific_ops
    return await scientific_ops.plot_contourf(X, Y, Z, levels, title, figsize)

@mcp.tool()
async def plot_heatmap(data: DataInput, title: Optional[str] = None, cmap: str = 'viridis', figsize: List[int] = [10, 8]) -> str: 
    """RENDERS a color-coded heatmap to visualize matrix data and cross-correlations. [ACTION]
    
    [RAG Context]
    The absolute "Matrix Intelligence Super Tool" for identifying patterns in multi-dimensional arrays. A heatmap transforms a sea of numbers into a visual "Color Map" where high values are hot and low values are cold. It is most famously used for "Correlation Matrices" (seeing which features move together), "Confusion Matrices" (evaluating machine learning model errors), and "Customer Journey Heatmaps" (identifying high-traffic areas on a website). It allows the reasoning kernel to instantly spot "Hotspots" and anomalies in massive spreadsheets that would be impossible to see in raw text.
    
    How to Use:
    - 'data': A 2D array or matrix.
    - 'cmap': The color scheme (e.g., 'magma', 'coolwarm', 'RdYlGn').
    - Essential for financial risk modeling, genomic heatmaps, and identifying seasonal spikes in time-series grids.
    
    Keywords: heatmap, matrix visualization, correlation map, hotspot discovery, color grid, intensity visualization.
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
    """CREATES a true 3D scatter plot to visualize the interaction between three independent variables. [ACTION]
    
    [RAG Context]
    An elite "Multi-Variable Analysis Super Tool" that breaks the 2D barrier. By adding a Z-axis, this plot allows the system to identify "Spatial Clusters" and "Complex Planes" that are invisible in flat 2D scatter plots. It is the primary tool for "3D Anomaly Detection" (identification of points that are outliers across three metrics simultaneously) and "3D Segmentation" (grouping users based on Age, Income, and Spending). It provides a high-fidelity visual experience that effectively communicates the complexity of high-dimensional data relationships.
    
    How to Use:
    - 'x', 'y', 'z': Three numerical arrays of equal length.
    - Yields a PNG image showing the 3D projection, helping the user understand "Depth" in their data.
    - Ideal for physical modeling, cluster validation, and advanced demographic research.
    
    Keywords: 3d scatter, xyz plot, spatial visualization, multi-variable clustering, depth analysis, 3d relationship mapping.
    """
    from mcp_servers.matplotlib_server.tools import three_d_ops
    return await three_d_ops.plot_scatter3d(x, y, z, title, figsize)

@mcp.tool()
async def plot_surface(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """PLOTS 3D surface. [ACTION]
    
    [RAG Context]
    An advanced "Super Tool" for multi-dimensional modeling. It generates a smooth 3D surface plot representing the relationship between three variables (X, Y mapped to coordinates, Z to elevation).
    
    How to Use:
    - Expects 2D arrays (meshgrids) for X, Y, and Z.
    - Essential for visualizing complex functions, terrains, or surface response models.
    
    Keywords: 3d surface, mesh plot, topographical visualization, xyz modeling.
    """
    from mcp_servers.matplotlib_server.tools import three_d_ops
    return await three_d_ops.plot_surface(X, Y, Z, title, figsize)

@mcp.tool()
async def plot_wireframe(X: DataInput, Y: DataInput, Z: DataInput, title: Optional[str] = None, figsize: List[int] = [10, 8]) -> str: 
    """DRAWS a 3D wireframe mesh representing a mathematical surface or structural grid. [ACTION]
    
    [RAG Context]
    A high-speed "3D structural Super Tool" for visualizing the framework of a surface. Unlike a solid 'plot_surface', the wireframe only shows the connecting lines of the grid, making it much more computationally efficient and often easier to interpret when looking at multiple overlapping surfaces. It is the primary tool for "Structural Engineering Visualization," "Network Latency Grids," and "Surface Trend Modeling" where seeing the underlying mesh structure is more important than the surface color alone.
    
    How to Use:
    - Requires 2D meshgrids (X, Y) and a 2D data array (Z).
    - Lightweight and fast to render compared to shaded surfaces.
    - Excellent for showing the "Skeleton" of complex functions or predictive surface models.
    
    Keywords: wireframe plot, 3d mesh, structural grid, surface framework, xyz skeleton, grid visualization.
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
    """CREATES a custom multi-chart mosaic layout using semantic positioning. [ACTION]
    
    [RAG Context]
    A specialized "Layout Orchestration Super Tool" for building complex infographics and scientific posters. Unlike simple grids, a mosaic allows the system to define "Areas" of different sizes using a simple string map (e.g., 'AAB;CCD'). This tool allows the AI to design a custom dashboard where a main 'Summary' chart takes up the top half, while multiple smaller 'Detail' charts are arranged below. It is the primary way the Kea system organizes its visual findings into a professional, easy-to-read narrative.
    
    How to Use:
    - 'layout': A string representation of the grid (e.g., `"AA;BC"`).
    - 'plots': A dictionary mapping the labels in the layout ('A', 'B', 'C') to the function calls and data needed for those sub-plots.
    - Yields a single high-resolution image containing the entire orchestrated layout.
    
    Keywords: mosaic layout, dashboard design, subplot orchestration, grid mapping, visual narrative, infographics builder.
    """
    from mcp_servers.matplotlib_server.tools import layout_ops
    return await layout_ops.create_mosaic(layout, plots, figsize, title)

@mcp.tool()
async def create_animation(frames_data: List[DataInput], plot_type: str = 'line', x: Optional[DataInput] = None, title: Optional[str] = None, interval: int = 200, figsize: List[int] = [10, 6]) -> str: 
    """GENERATES a dynamic video or GIF animation to visualize time-evolving datasets. [ACTION]
    
    [RAG Context]
    An elite "Temporal Dynamics Super Tool" used for demonstrating change over time in a way that static charts cannot. It essentially creates a "Movie" of your data, allowing the system to show how a stock price fluctuated, how a heat-map shifted across a warehouse floor, or how a machine learning model converged during training. In the corporate kernel, this is used for high-impact presentations and for auditing high-frequency sensor data where the "Flow" of data is as important as its final state.
    
    How to Use:
    - 'frames_data': A list of datasets, one for each frame of the animation.
    - 'interval': Time in milliseconds between each frame.
    - Result is returned as a path to an MP4 or GIF file which can be embedded in reports.
    
    Keywords: data animation, temporal video, dynamic visualization, time-lapse chart, series flow, gif generator.
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
    """RENDERS a Sankey diagram to visualize the flow of energy, money, or materials through a system. [ACTION]
    
    [RAG Context]
    The ultimate "Flow Intelligence Super Tool" for supply chain and financial auditing. A Sankey diagram uses lines of varying widths to show the magnitude of transfer between entities. It is the primary tool for "Budget Auditing" (seeing how revenue is split into different departments), "Supply Chain Logistics" (mapping the flow of goods from factory to customer), and "Energy Audits" (visualizing losses in a power system). It allows the reasoning kernel to instantly identify "Bottlenecks" and "Leaks" in any corporate process that involves the movement of resources.
    
    How to Use:
    - 'flows': A list of numerical values where positive values represent inputs and negative values represent outputs (e.g., `[100, -50, -30, -20]`).
    - 'labels': Names for each flow branch.
    - Essential for understanding the "Life Cycle" of capital and materials within the corporation.
    
    Keywords: sankey diagram, flow visualization, resource mapping, budget audit, supply chain flow, transfer diagram.
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
    The ultimate "Super Tool" for comprehensive data reporting. It orchestrates multiple independent Matplotlib charts into a single cohesive grid layout.
    
    How to Use:
    - 'plots': A list of dictionaries, each specifying the tool name and arguments for a sub-plot.
    - 'layout': [rows, columns] grid configuration.
    - Ideal for summarising an entire analysis in one visual snapshot.
    
    Keywords: multi-plot grid, visual summary, analytical dashboard, report generator.
    """
    from mcp_servers.matplotlib_server.tools import super_ops
    return await super_ops.create_dashboard(plots, layout, figsize)

@mcp.tool()
async def set_style(style: str) -> str: 
    """APPLIES a global aesthetic theme to all subsequent plots for professional consistency. [ACTION]
    
    [RAG Context]
    A vital "Brand & Clarity Super Tool" for ensuring that all visual artifacts match the corporate design standards. Matplotlib can look "clinical" by default; this tool allows the system to switch to high-quality themes like 'seaborn' (for soft, modern statistical plots), 'ggplot' (for academic-grade aesthetics), or 'dark_background' (for high-contrast dashboards). This is a mandatory requirement for generating "Investor-Ready" reports where the visual professionalism of the data is as important as the data itself.
    
    How to Use:
    - 'style': A valid style string (use 'get_styles' to see the full list of available themes on this machine).
    - Affects colors, fonts, gridlines, and backgrounds for all following chart generation calls.
    
    Keywords: plotting style, visual theme, chart aesthetics, seaborn theme, ggplot style, dashboard design.
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

