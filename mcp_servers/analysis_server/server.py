# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import stats_ops
import structlog
from typing import List, Dict, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("analysis_server")

@mcp.tool()
def meta_analysis(data_points: List[Dict[str, Any]], analysis_type: str = "comparison") -> str:
    """Perform meta-analysis across multiple data sources.
    Args:
        data_points: List of data points with source, value, and metadata
        analysis_type: Type: comparison, consensus, variance, aggregate
    """
    return stats_ops.meta_analysis(data_points, analysis_type)

@mcp.tool()
def trend_detection(data: List[Union[Dict, float, int]], metric_name: str = "Value", detect_anomalies: bool = True) -> str:
    """Detect trends, patterns, and anomalies in time-series data.
    Args:
        data: Time-series data as [{date, value}] or numeric array
        metric_name: Name of the metric being analyzed
        detect_anomalies: Whether to detect anomalies
    """
    return stats_ops.trend_detection(data, metric_name, detect_anomalies)

if __name__ == "__main__":
    mcp.run()
