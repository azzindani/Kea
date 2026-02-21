
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
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.visualization_server.tools import (
    plotly_chart, heatmap, distribution, pairplot
)
import structlog
from typing import Optional, List, Any

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

mcp = FastMCP("visualization_server", dependencies=["plotly", "pandas", "numpy", "kaleido"])

@mcp.tool()
async def create_plotly_chart(data_url: str, chart_type: str, x_column: Optional[str] = None, y_column: Optional[str] = None, color_column: Optional[str] = None, title: Optional[str] = None) -> str:
    """PLOTS plotly chart. [ACTION]
    
    [RAG Context]
    Create interactive Plotly chart (line, bar, scatter, etc.).
    Returns chart JSON/HTML.
    """
    return await plotly_chart.plotly_chart(data_url, chart_type, x_column, y_column, color_column, title)

@mcp.tool()
async def create_correlation_heatmap(data_url: str, title: str = "Correlation Heatmap") -> str:
    """PLOTS heatmap. [ACTION]
    
    [RAG Context]
    Create correlation heatmap.
    Returns chart JSON/HTML.
    """
    return await heatmap.correlation_heatmap(data_url, title)

@mcp.tool()
async def create_distribution_plot(data_url: str, columns: Optional[List[str]] = None) -> str:
    """PLOTS distribution. [ACTION]
    
    [RAG Context]
    Create distribution/histogram plots.
    Returns chart JSON/HTML.
    """
    return await distribution.distribution_plot(data_url, columns)

@mcp.tool()
async def create_pairplot(data_url: str, columns: Optional[List[str]] = None, color_column: Optional[str] = None) -> str:
    """PLOTS pairplot. [ACTION]
    
    [RAG Context]
    Create pairwise scatter plot matrix.
    Returns chart JSON/HTML.
    """
    return await pairplot.pairplot(data_url, columns, color_column)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class VisualizationServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
