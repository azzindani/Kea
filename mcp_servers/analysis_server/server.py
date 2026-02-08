
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.analysis_server.tools import stats_ops
import structlog
from typing import List, Dict, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("analysis_server")

@mcp.tool()
def meta_analysis(data_points: List[Dict[str, Any]], analysis_type: str = "comparison") -> str:
    """PERFORMS meta-analysis across sources. [ENTRY]
    
    [RAG Context]
    Aggregates and compares data from multiple inputs.
    Args:
        analysis_type: "comparison", "consensus", "variance", "aggregate".
    """
    return stats_ops.meta_analysis(data_points, analysis_type)

@mcp.tool()
def trend_detection(data: List[Union[Dict, float, int]], metric_name: str = "Value", detect_anomalies: bool = True) -> str:
    """DETECTS trends and anomalies in time-series. [ENTRY]
    
    [RAG Context]
    Args:
        data: List of values or dicts with date/value.
        detect_anomalies: If True, flags outliers.
    """
    return stats_ops.trend_detection(data, metric_name, detect_anomalies)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class AnalysisServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
