
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
from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    relational_ops, distribution_ops, categorical_ops, 
    regression_ops, matrix_ops, multiples_ops, 
    style_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

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
    High-level interface for scatter and line plots.
    Returns path to saved image.
    """
    return await relational_ops.relplot(data, x, y, hue, style, size, col, row, kind, height, aspect)

@mcp.tool()
async def scatterplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS scatter chart. [ACTION]
    
    [RAG Context]
    Standard scatter plot with semantic mapping.
    Returns path to saved image.
    """
    return await relational_ops.scatterplot(data, x, y, hue, style, size, title)

@mcp.tool()
async def lineplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, style: Optional[str] = None, size: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS line chart. [ACTION]
    
    [RAG Context]
    Standard line plot with semantic mapping.
    Returns path to saved image.
    """
    return await relational_ops.lineplot(data, x, y, hue, style, size, title)

# ==========================================
# 2. Distribution
# ==========================================
@mcp.tool()
async def displot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, row: Optional[str] = None, col: Optional[str] = None, kind: str = 'hist', height: float = 5, aspect: float = 1) -> str: 
    """PLOTS distribution chart. [ACTION]
    
    [RAG Context]
    High-level interface for histograms and KDEs.
    Returns path to saved image.
    """
    return await distribution_ops.displot(data, x, y, hue, row, col, kind, height, aspect)

@mcp.tool()
async def histplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, bins: Union[int, str] = 'auto', kde: bool = False, title: Optional[str] = None) -> str: 
    """PLOTS histogram. [ACTION]
    
    [RAG Context]
    Standard histogram with optional KDE.
    Returns path to saved image.
    """
    return await distribution_ops.histplot(data, x, y, hue, bins, kde, title)

@mcp.tool()
async def kdeplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, fill: bool = False, title: Optional[str] = None) -> str: 
    """PLOTS KDE chart. [ACTION]
    
    [RAG Context]
    Kernel Density Estimation plot.
    Returns path to saved image.
    """
    return await distribution_ops.kdeplot(data, x, y, hue, fill, title)

@mcp.tool()
async def ecdfplot(data: DataInput, x: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS ECDF chart. [ACTION]
    
    [RAG Context]
    Empirical Cumulative Distribution Function plot.
    Returns path to saved image.
    """
    return await distribution_ops.ecdfplot(data, x, hue, title)

@mcp.tool()
async def rugplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, height: float = 0.05) -> str: 
    """PLOTS rug plot. [ACTION]
    
    [RAG Context]
    Marginal distribution plot.
    Returns path to saved image.
    """
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
    return await categorical_ops.catplot(data, x, y, hue, row, col, kind, height, aspect)

@mcp.tool()
async def boxplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS boxplot. [ACTION]
    
    [RAG Context]
    Standard boxplot with semantic mapping.
    Returns path to saved image.
    """
    return await categorical_ops.boxplot(data, x, y, hue, title)

@mcp.tool()
async def violinplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, split: bool = False, title: Optional[str] = None) -> str: 
    """PLOTS violin plot. [ACTION]
    
    [RAG Context]
    Violin plot for categorical distribution.
    Returns path to saved image.
    """
    return await categorical_ops.violinplot(data, x, y, hue, split, title)

@mcp.tool()
async def barplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS bar chart. [ACTION]
    
    [RAG Context]
    Bar plot with error bars.
    Returns path to saved image.
    """
    return await categorical_ops.barplot(data, x, y, hue, title)

@mcp.tool()
async def countplot(data: DataInput, x: Optional[str] = None, y: Optional[str] = None, hue: Optional[str] = None, title: Optional[str] = None) -> str: 
    """PLOTS count plot. [ACTION]
    
    [RAG Context]
    Count of observations in each categorical bin.
    Returns path to saved image.
    """
    return await categorical_ops.countplot(data, x, y, hue, title)

# ==========================================
# 4. Regression
# ==========================================
@mcp.tool()
async def lmplot(data: DataInput, x: str, y: str, hue: Optional[str] = None, col: Optional[str] = None, row: Optional[str] = None, height: float = 5, aspect: float = 1) -> str: 
    """PLOTS linear model. [ACTION]
    
    [RAG Context]
    High-level interface for regression plots.
    Returns path to saved image.
    """
    return await regression_ops.lmplot(data, x, y, hue, col, row, height, aspect)

@mcp.tool()
async def regplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: 
    """PLOTS regression chart. [ACTION]
    
    [RAG Context]
    Standard regression plot with confidence interval.
    Returns path to saved image.
    """
    return await regression_ops.regplot(data, x, y, title)

@mcp.tool()
async def residplot(data: DataInput, x: str, y: str, title: Optional[str] = None) -> str: 
    """PLOTS residuals. [ACTION]
    
    [RAG Context]
    Residuals of a linear regression.
    Returns path to saved image.
    """
    return await regression_ops.residplot(data, x, y, title)

# ==========================================
# 5. Matrix & Multiples
# ==========================================
@mcp.tool()
async def heatmap(data: DataInput, annot: bool = False, cmap: str = 'viridis', title: Optional[str] = None) -> str: 
    """PLOTS heatmap. [ACTION]
    
    [RAG Context]
    Heatmap of rectangular data.
    Returns path to saved image.
    """
    return await matrix_ops.heatmap(data, annot, cmap, title)

@mcp.tool()
async def clustermap(data: DataInput, cmap: str = 'viridis', standard_scale: Optional[int] = None) -> str: 
    """PLOTS clustermap. [ACTION]
    
    [RAG Context]
    Heatmap with hierarchical clustering.
    Returns path to saved image.
    """
    return await matrix_ops.clustermap(data, cmap, standard_scale)

@mcp.tool()
async def pairplot(data: DataInput, hue: Optional[str] = None, kind: str = 'scatter', diag_kind: str = 'auto') -> str: 
    """PLOTS pairplot. [ACTION]
    
    [RAG Context]
    Pairwise relationships in a dataset.
    Returns path to saved image.
    """
    return await multiples_ops.pairplot(data, hue, kind, diag_kind)

@mcp.tool()
async def jointplot(data: DataInput, x: str, y: str, kind: str = 'scatter', hue: Optional[str] = None) -> str: 
    """PLOTS jointplot. [ACTION]
    
    [RAG Context]
    Bivariate plot with marginal distributions.
    Returns path to saved image.
    """
    return await multiples_ops.jointplot(data, x, y, kind, hue)

# ==========================================
# 6. Style & Super
# ==========================================
@mcp.tool()
async def set_theme(style: str = "darkgrid", palette: str = "deep", font_scale: float = 1.0) -> str: 
    """SETS global theme. [ACTION]
    
    [RAG Context]
    Sets seaborn visual theme parameters.
    """
    return await style_ops.set_theme(style, palette, font_scale)

@mcp.tool()
async def get_palette(palette: str = "deep", n_colors: int = 10, as_hex: bool = True) -> List[Any]: 
    """GETS color palette. [DATA]
    
    [RAG Context]
    Returns list of colors in a palette.
    """
    return await style_ops.get_palette(palette, n_colors, as_hex)

@mcp.tool()
async def auto_plot(data: DataInput, x: str, y: Optional[str] = None) -> str: 
    """PLOTS automatically. [ACTION]
    
    [RAG Context]
    Infers best plot type from data.
    Returns path to saved image.
    """
    return await super_ops.auto_plot(data, x, y)

@mcp.tool()
async def create_dashboard(data: DataInput, plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str: 
    """CREATES dashboard. [ACTION]
    
    [RAG Context]
    Combines multiple plots into a dashboard.
    Returns path to saved image.
    """
    return await super_ops.create_dashboard(data, plots, layout, figsize)

if __name__ == "__main__":
    mcp.run()