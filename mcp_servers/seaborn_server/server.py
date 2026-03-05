
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
# from mcp_servers.seaborn_server.tools import (
#     relational_ops, distribution_ops, categorical_ops, 
#     regression_ops, matrix_ops, multiples_ops, 
#     style_ops, super_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("seaborn_server", dependencies=["seaborn", "matplotlib", "pandas", "numpy", "scipy"])
DataInput = Union[List[List[Any]], List[Dict[str, Any]], str, Dict[str, Any]]
VectorInput = Union[List[Any], str]

# ==========================================
# 1. Relational
# ==========================================
@mcp.tool()
async def relplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, kind: str = 'scatter', height: float = 5, aspect: float = 1) -> str: 
    """PLOTS relational chart. [ACTION]
    
    [RAG Context]
    A high-level "Super Tool" for multi-dimensional relationship discovery. It provides a unified interface for creating scatter and line plots, with built-in support for categorical faceting and semantic mapping.
    
    How to Use:
    - 'hue', 'style', 'size': Map variables to visual attributes.
    - 'col', 'row': Facet the chart across multiple subplots based on categorical variables.
    - Perfect for complex datasets where relationships change across groups.
    
    Keywords: relational plot, multi-axis scatter, faceted line chart, semantic mapping.
    """
    from mcp_servers.seaborn_server.tools import relational_ops
    return await relational_ops.relplot(data, x, y, hue, style, size, col, row, kind, height, aspect)

@mcp.tool()
async def scatterplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: 
    """CREATES a high-quality scatter plot with complex semantic mapping for relational analysis. [ACTION]
    
    [RAG Context]
    An elite "Semantic Relationship Super Tool" that builds upon basic Matplotlib scatter plots with professional-grade data mapping. Unlike standard plots, Seaborn's scatterplot handles category alignment and legend generation automatically. It is the primary tool for "Multi-Dimensional Correlation" where you want to see how two numeric variables (X and Y) interact, while simultaneously viewing a third categorical variable (via 'hue') and a fourth numeric variable (via 'size'). It is a mandatory requirement for serious exploratory data analysis in the corporate kernel.
    
    How to Use:
    - 'hue': Assign a categorical column to differentiate points by color.
    - 'size': Assign a numerical column to create a "Bubble Chart" effect.
    - 'style': Assign a categorical column to differentiate groups by marker shape (dots, crosses, etc.).
    - Essential for identifying non-linear patterns and group-specific outliers.
    
    Keywords: seaborn scatter, semantic mapping, relationship plot, multi-dimensional discovery, correlation visualization, bubble chart.
    """
    from mcp_servers.seaborn_server.tools import relational_ops
    return await relational_ops.scatterplot(data, x, y, hue, style, size, title)

@mcp.tool()
async def lineplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS line chart. [ACTION]
    
    [RAG Context]
    Standard line plot with semantic mapping.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import relational_ops
    return await relational_ops.lineplot(data, x, y, hue, style, size, title)

# ==========================================
# 2. Distribution
# ==========================================
@mcp.tool()
async def displot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'hist', height: float = 5, aspect: float = 1) -> str: 
    """PLOTS distribution chart. [ACTION]
    
    [RAG Context]
    A robust "Super Tool" for statistical distribution modeling. It offers a facetable interface for visualizing the distribution of numeric data through histograms, KDEs, or ECDF plots.
    
    How to Use:
    - 'kind': Choose 'hist' (histogram), 'kde' (kernel density), or 'ecdf'.
    - Ideal for comparing distributions across multiple categories using 'row' or 'col' faceting.
    
    Keywords: distribution analysis, data density, statistical freq, comparative histogram.
    """
    from mcp_servers.seaborn_server.tools import distribution_ops
    return await distribution_ops.displot(data, x, y, hue, row, col, kind, height, aspect)

@mcp.tool()
async def histplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, bins: Union[int, str] = 'auto', kde: bool = False, title: Optional[str] = None) -> str: 
    """GENERATES a statistically rigorous histogram to visualize the distribution of datasets. [ACTION]
    
    [RAG Context]
    A premier "Statistical Profiling Super Tool" that provides a clean, professional view of data density. While basic histograms only show counts, Seaborn's version handles overlapping distributions with grace, using 'hue' to compare relative frequencies between groups (like "Sales Distribution of Product A vs Product B"). It is the mandatory tool for "Univariate Analysis," allowing the system to determine if a dataset is normally distributed, skewed, or contains hidden sub-populations. This knowledge is critical for choosing the right statistical tests or machine learning algorithms.
    
    How to Use:
    - 'bins': Control the granularity of the distribution buckets.
    - 'kde': Set to True to overlay a "Kernel Density Estimate" curve for a smooth "Trend Line" of the probability density.
    - Ideal for identifying data quality issues, like unexpected spikes or gaps in a numerical sequence.
    
    Keywords: statistical histogram, data distribution, density analysis, frequency profile, comparative distribution, univariate plot.
    """
    from mcp_servers.seaborn_server.tools import distribution_ops
    return await distribution_ops.histplot(data, x, y, hue, bins, kde, title)

@mcp.tool()
async def kdeplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, fill: bool = False, title: Optional[str] = None) -> str: 
    """RENDERS a smooth Kernel Density Estimate (KDE) to visualize the probability distribution of a variable. [ACTION]
    
    [RAG Context]
    A sophisticated "Continuous Density Super Tool" for advanced statistical reporting. Unlike a histogram which produces "Steps," the KDE uses a kernel to create a smooth, continuous probability curve. This is essential for identifying the "True Shape" of a distribution without the distraction of arbitrary bin boundaries. In the Kea corporate system, KDE plots are used for high-purity scientific analysis, such as "Network Latency Profiling" or "Financial Return Distribution," where understanding the "Probability Peaking" is more important than raw counts.
    
    How to Use:
    - 'fill': Set to True to shade the area under the curve for a more premium, publication-ready appearance.
    - 'hue': Use to compare the smooth shapes of different data populations (e.g., "Active Users" vs "Churned Users").
    - Essential for detecting bimodal or multi-modal distributions that indicate the presence of hidden subgroups.
    
    Keywords: kde plot, kernel density, probability curve, smooth distribution, continuous density, distribution shape.
    """
    from mcp_servers.seaborn_server.tools import distribution_ops
    return await distribution_ops.kdeplot(data, x, y, hue, fill, title)

@mcp.tool()
async def ecdfplot(data: DataInput, x: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS ECDF chart. [ACTION]
    
    [RAG Context]
    Empirical Cumulative Distribution Function plot.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import distribution_ops
    return await distribution_ops.ecdfplot(data, x, hue, title)

@mcp.tool()
async def rugplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, height: float = 0.05) -> str: 
    """PLOTS rug plot. [ACTION]
    
    [RAG Context]
    Marginal distribution plot.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import distribution_ops
    return await distribution_ops.rugplot(data, x, y, hue, height)

# ==========================================
# 3. Categorical
# ==========================================
@mcp.tool()
async def catplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'strip', height: float = 5, aspect: float = 1) -> str: 
    """PLOTS categorical chart. [ACTION]
    
    [RAG Context]
    High-level interface for categorical plots.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import categorical_ops
    return await categorical_ops.catplot(data, x, y, hue, row, col, kind, height, aspect)

@mcp.tool()
async def boxplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """GENERATES a professional-grade box-and-whisker plot for categorical comparison. [ACTION]
    
    [RAG Context]
    An elite "Statistical Comparison Super Tool" for analyzing variance across different business categories. While Matplotlib's boxplot is functional, Seaborn's version is designed for direct DataFrame interaction and advanced semantic grouping via 'hue'. It provides an instant visual summary of the five-number statistical summary (min, Q1, median, Q3, max) along with a clear identification of "Outliers." It is the mandatory tool for "Internal Auditing"—for example, comparing the "Processing Time" across different corporate departments or "Product Quality" across different manufacturing batches.
    
    How to Use:
    - 'x' & 'y': Assign one to a categorical axis and the other to a numerical axis.
    - 'hue': Differentiate the boxes within each category by a second categorical variable (e.g., comparing "Male" vs "Female" performance within each "Department").
    - Essential for validating consistency and identifying high-variance processes.
    
    Keywords: seaborn boxplot, whisker plot, categorical statistics, variance comparison, outlier audit, distribution summary.
    """
    from mcp_servers.seaborn_server.tools import categorical_ops
    return await categorical_ops.boxplot(data, x, y, hue, title)

@mcp.tool()
async def violinplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, split: bool = False, title: Optional[str] = None) -> str: 
    """CREATES an information-rich violin plot combining boxplot data with kernel density. [ACTION]
    
    [RAG Context]
    A sophisticated "High-Density Comparison Super Tool" for technical data analysis. Unlike a boxplot, the violin plot reveals the complete "Probability Map" for each category, making it obvious if a group is bimodal or has a unique internal distribution shape. In the Kea corporate system, this is the preferred tool for "Complex Demographics" and "Scientific Telemetry," allowing the AI to see the full "Breadth" of behaviors within a group rather than just the quartiles. It communicates a much deeper level of "Data Nuance" than a traditional bar or box chart.
    
    How to Use:
    - 'split': When using 'hue' with two categories, setting 'split=True' draws half a violin for each category on a single axis, allowing for direct, side-by-side density comparison.
    - Ideal for comparing "Pre-Optimization" vs "Post-Optimization" results across multiple project categories.
    
    Keywords: violin plot, density comparison, probability shape, multimodal analysis, semantic scaling, distribution visualization.
    """
    from mcp_servers.seaborn_server.tools import categorical_ops
    return await categorical_ops.violinplot(data, x, y, hue, split, title)

@mcp.tool()
async def barplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """RENDERS a publication-quality bar chart with automated error-bar estimation. [ACTION]
    
    [RAG Context]
    A robust "Executive Comparison Super Tool" for visualizing categorical aggregates. Unlike a basic chart, Seaborn's barplot automatically calculates a "Confidence Interval" (error bars) if there are multiple observations per category. This is critical for business decision-making because it shows not just the "Average" performance, but how "Reliable" that average is. It is the mandatory tool for "Quarterly Summaries" and "Regional Comparisons" where identifying the stability of a trend is as important as the trend itself.
    
    How to Use:
    - 'x' & 'y': Map categorical and numerical columns.
    - Seaborn will automatically group and average the data if multiple records exist for the same 'x' value.
    - Yields a clean, authoritative visual suitable for formal corporate reports and presentation decks.
    
    Keywords: seaborn barplot, categorical mean, confidence intervals, reliable comparison, aggregate visualization, business chart.
    """
    from mcp_servers.seaborn_server.tools import categorical_ops
    return await categorical_ops.barplot(data, x, y, hue, title)

@mcp.tool()
async def countplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS count plot. [ACTION]
    
    [RAG Context]
    Count of observations in each categorical bin.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import categorical_ops
    return await categorical_ops.countplot(data, x, y, hue, title)

# ==========================================
# 4. Regression
# ==========================================
@mcp.tool()
async def lmplot(data: DataInput, x: str, y: str, hue: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, height: float = 5, aspect: float = 1) -> str: 
    """PERFORMS a faceted linear regression analysis to visualize trends across multiple groups. [ACTION]
    
    [RAG Context]
    The ultimate "Predictive Insight Super Tool" for complex datasets. 'lmplot' (Linear Model Plot) doesn't just show points; it fits a regression line AND its confidence interval—automatically. Most powerfully, it can "Facet" the analysis, meaning it can draw separate regression lines for different categories (e.g., seeing one trend line for "Enterprise Customers" and another for "Retail Customers" on the same grid). It is the mandatory tool for "Market Segmentation Trends" and "Impact Analysis," allowing the system to visually prove if a relationship holds true across different branches or time periods.
    
    How to Use:
    - 'x' & 'y': The numerical features to regress.
    - 'col', 'row': Use to create a grid of plots, each representing a unique category.
    - Essential for discovering "Group-Specific Behaviors" that are lost in a single global trend line.
    
    Keywords: linear model, faceted regression, trend discovery, impact analysis, group trends, predictive visualization.
    """
    from mcp_servers.seaborn_server.tools import regression_ops
    return await regression_ops.lmplot(data, x, y, hue, col, row, height, aspect)

@mcp.tool()
async def regplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: 
    """PLOTS regression chart. [ACTION]
    
    [RAG Context]
    Standard regression plot with confidence interval.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import regression_ops
    return await regression_ops.regplot(data, x, y, title)

@mcp.tool()
async def residplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: 
    """PLOTS residuals. [ACTION]
    
    [RAG Context]
    Residuals of a linear regression.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import regression_ops
    return await regression_ops.residplot(data, x, y, title)

# ==========================================
# 5. Matrix & Multiples
# ==========================================
@mcp.tool()
async def heatmap(data: DataInput, annot: bool = False, cmap: str = 'viridis', title: Optional[str] = None) -> str: 
    """PLOTS heatmap. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for matrix and correlation visualization. It renders rectangular data as a color-encoded grid, identifying magnitude and clusters in dense numerical tables.
    
    How to Use:
    - 'annot': If True, writes the numeric value into each cell.
    - 'cmap': Controls the color progression (e.g., 'magma', 'coolwarm' for correlations).
    - Perfect for visualizing correlation matrices, confusion matrices, or time-series intensity.
    
    Keywords: intensity grid, matrix plot, correlation heatmap, color coded table.
    """
    from mcp_servers.seaborn_server.tools import matrix_ops
    return await matrix_ops.heatmap(data, annot, cmap, title)

@mcp.tool()
async def clustermap(data: DataInput, cmap: str = 'viridis', standard_scale: Optional[int] = None) -> str: 
    """GENERATES a hierarchical clustered heatmap to discover groups and relationships in matrix data. [ACTION]
    
    [RAG Context]
    A world-class "Knowledge Discovery Super Tool" used for unsupervised pattern recognition in complex tables. Unlike a standard heatmap, a clustermap uses mathematical clustering (Linkage) to reorder rows and columns so that similar items are placed next to each other. This reveals "Natural Groupings" and "Block Structures" in your data that are otherwise invisible. It is the primary tool for "Genomic Analysis" (grouping genes with similar expression), "Customer Segmentation" (grouping users with similar purchase vectors), and "Asset Correlation" in finance.
    
    How to Use:
    - 'standard_scale': Set to 0 (rows) or 1 (columns) to normalize data, ensuring that features with different units (e.g., Age vs Salary) can be compared fairly.
    - Resulting image includes "Dendrograms" (tree diagrams) on the sides, illustrating the strength of the relationships between clustered groups.
    
    Keywords: clustermap, hierarchical clustering, dendrogram visualization, matrix grouping, similarity discovery, cluster analysis.
    """
    from mcp_servers.seaborn_server.tools import matrix_ops
    return await matrix_ops.clustermap(data, cmap, standard_scale)

@mcp.tool()
async def pairplot(data: DataInput, hue: Optional[str] = None, kind: str = 'scatter', diag_kind: str = 'auto') -> str: 
    """REVIEWS all pairwise relationships across an entire dataset in a high-density grid. [ACTION]
    
    [RAG Context]
    The absolute "System-Wide Inspection Super Tool" for high-dimensional data discovery. A pairplot creates a grid of charts where every numeric column in your dataset is plotted against every other column. This allows the AI and the user to see "The Big Picture" in one glance—identifying which variables correlate, which are redundant, and which contain unique clusters. It is the mandatory first step for any "Deep Data Audit" or before training a high-stakes multivariate model, ensuring no hidden relationship is missed.
    
    How to Use:
    - 'hue': Use a categorical column to color-code the entire grid, making it instantly obvious how different groups (e.g., "Premium" vs "Basic" users) occupy the data space.
    - 'kind': Choose 'scatter' or 'reg' (to include trend lines in every plot).
    - WARNING: Can be slow and image-heavy for datasets with many columns (>10).
    
    Keywords: pairplot, pairwise relationships, scatter matrix, multivariate audit, dataset overview, correlation grid.
    """
    from mcp_servers.seaborn_server.tools import multiples_ops
    return await multiples_ops.pairplot(data, hue, kind, diag_kind)

@mcp.tool()
async def jointplot(data: DataInput, x: str, y: str, kind: str = 'scatter', hue: Optional[str] = None) -> str: 
    """PERFORMS a dual-axis analysis of two variables, showing both their relationship and individual distributions. [ACTION]
    
    [RAG Context]
    A clever "Multi-Perspective Super Tool" for high-precision bivariate analysis. A jointplot creates a central relationship chart (e.g., Scatter) while simultaneously rendering the individual "Marginal Distributions" (Histograms or KDEs) on the top and right axes. This allows the system to answer: "Does the relationship between X and Y hold true across the entire range, or only where the data is most dense?" It is essential for "Financial Risk Analysis" and "Engineering Precision Checks" where understanding the interaction of two variables is only half the story.
    
    How to Use:
    - 'kind': Choose 'scatter', 'reg' (regression), 'hex' (for dense data), or 'kde' (for smooth contours).
    - Perfect for situations where you want to see the correlation between two metrics while keeping an eye on their individual "Health" and spread.
    
    Keywords: jointplot, bivariate distribution, marginal plot, interactive visualization, dual-axis analysis, correlation perspective.
    """
    from mcp_servers.seaborn_server.tools import multiples_ops
    return await multiples_ops.jointplot(data, x, y, kind, hue)

# ==========================================
# 6. Style & Super
# ==========================================
@mcp.tool()
async def set_theme(style: str = "darkgrid", palette: str = "deep", font_scale: float = 1.0) -> str: 
    """CONFIGURES the global aesthetic and font parameters for institutional-grade visualization. [ACTION]
    
    [RAG Context]
    A vital "Corporate Identity Super Tool" for ensuring all generated charts meet a consistent, professional standard. Seaborn themes control not just colors, but grid styles, axes line weights, and font sizes. This allows the system to produce charts that look modern, readable, and "Premium" across all departments. It is a mandatory requirement for building a cohesive "Visual Presence" in automated reporting workflows, ensuring that an analysis performed by an AI looks just as polished as one created by a senior designer.
    
    How to Use:
    - 'style': 'darkgrid' (standard), 'whitegrid' (clean), 'dark', 'white', or 'ticks'.
    - 'palette': Controls the default grouping colors (e.g., 'muted', 'bright', 'colorblind').
    - 'font_scale': Increases readable size for mobile dashboards or low-resolution presentations.
    
    Keywords: visualization theme, global chart style, seaborn theme, corporate branding, visual consistency, aesthetic config.
    """
    from mcp_servers.seaborn_server.tools import style_ops
    return await style_ops.set_theme(style, palette, font_scale)

@mcp.tool()
async def get_palette(palette: str = "deep", n_colors: int = 10, as_hex: bool = True) -> List[Any]: 
    """GETS color palette. [DATA]
    
    [RAG Context]
    Returns list of colors in a palette.
    """
    from mcp_servers.seaborn_server.tools import style_ops
    return await style_ops.get_palette(palette, n_colors, as_hex)

@mcp.tool()
async def auto_plot(data: DataInput, x: str, y: Optional[str] = None) -> str: 
    """PLOTS automatically. [ACTION]
    
    [RAG Context]
    An intelligent "Super Tool" for rapid prototyping. It analyzes the data types of the provided features and automatically chooses the most statistically appropriate Seaborn chart type.
    
    How to Use:
    - Simply provide a Dataset and the column names 'x' (and optionally 'y').
    - Returns a publication-quality chart (e.g., Histogram for univariate, Scatter/Box for bivariate).
    
    Keywords: automated graphing, smart plotter, heuristic chart select, fast EDA.
    """
    from mcp_servers.seaborn_server.tools import super_ops
    return await super_ops.auto_plot(data, x, y)

@mcp.tool()
async def create_dashboard(data: DataInput, plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str: 
    """CREATES dashboard. [ACTION]
    
    [RAG Context]
    Combines multiple plots into a dashboard.
    Returns path to saved image.
    """
    from mcp_servers.seaborn_server.tools import super_ops
    return await super_ops.create_dashboard(data, plots, layout, figsize)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class SeabornServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

