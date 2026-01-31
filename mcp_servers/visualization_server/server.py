# /// script
# dependencies = [
#   "kaleido",
#   "mcp",
#   "numpy",
#   "pandas",
#   "plotly",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    plotly_chart, heatmap, distribution, pairplot
)
import structlog
from typing import Optional, List, Any

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("visualization_server", dependencies=["plotly", "pandas", "numpy", "kaleido"])

@mcp.tool()
async def create_plotly_chart(data_url: str, chart_type: str, x_column: Optional[str] = None, y_column: Optional[str] = None, color_column: Optional[str] = None, title: Optional[str] = None) -> str:
    """Create interactive Plotly chart.
    Args:
        data_url: URL to CSV data
        chart_type: Type: line, bar, scatter, histogram, box, pie, heatmap
        x_column: X-axis column
        y_column: Y-axis column
        color_column: Column for color grouping
        title: Chart title
    """
    return await plotly_chart.plotly_chart(data_url, chart_type, x_column, y_column, color_column, title)

@mcp.tool()
async def create_correlation_heatmap(data_url: str, title: str = "Correlation Heatmap") -> str:
    """Create correlation heatmap.
    Args:
        data_url: URL to CSV data
        title: Chart title
    """
    return await heatmap.correlation_heatmap(data_url, title)

@mcp.tool()
async def create_distribution_plot(data_url: str, columns: Optional[List[str]] = None) -> str:
    """Create distribution/histogram plots.
    Args:
        data_url: URL to CSV data
        columns: Columns to plot (or 'all' numeric)
    """
    return await distribution.distribution_plot(data_url, columns)

@mcp.tool()
async def create_pairplot(data_url: str, columns: Optional[List[str]] = None, color_column: Optional[str] = None) -> str:
    """Create pairwise scatter plot matrix.
    Args:
        data_url: URL to CSV data
        columns: Columns to include
        color_column: Column for color
    """
    return await pairplot.pairplot(data_url, columns, color_column)

if __name__ == "__main__":
    mcp.run()
