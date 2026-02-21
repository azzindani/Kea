
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "numpy",
#   "pandas",
#   "scipy",
#   "structlog",
# ]
# ///


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.analytics_server.tools import eda, cleaning, stats
import structlog
import asyncio
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging()

# Dependencies: pandas, numpy, scipy, (optional: ydata-profiling)
mcp = FastMCP("analytics_server", dependencies=["pandas", "numpy", "scipy"])

async def run_op(op_func, diff_args=None, **kwargs):
    """Helper to run legacy tool ops."""
    try:
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        result = await op_func(**final_args)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
            
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# --- 1. EDA & Profiling ---
@mcp.tool()
async def eda_auto(
    data_url: str = None, 
    data: Dict[str, Any] = None, 
    target_column: str = None
) -> str:
    """ANALYZES data (EDA). [ACTION]
    
    [RAG Context]
    Perform automatic Exploratory Data Analysis.
    Returns analysis report.
    """
    return await run_op(eda.eda_auto, data_url=data_url, data=data, target_column=target_column)

@mcp.tool()
async def data_profiler(
    data_url: str, 
    minimal: bool = True
) -> str:
    """PROFILES data. [ACTION]
    
    [RAG Context]
    Generate detailed data profile report.
    Returns profile string.
    """
    return await run_op(eda.data_profiler, data_url=data_url, minimal=minimal)

# --- 2. Cleaning & Feature Engineering ---
@mcp.tool()
async def data_cleaner(
    data_url: str,
    handle_missing: str = "none",
    handle_outliers: str = "none",
    remove_duplicates: bool = False
) -> str:
    """CLEANS data. [ACTION]
    
    [RAG Context]
    Clean dataset: handle missing values, outliers, duplicates.
    Returns cleaned data summary.
    """
    return await run_op(cleaning.data_cleaner, data_url=data_url, handle_missing=handle_missing, handle_outliers=handle_outliers, remove_duplicates=remove_duplicates)

@mcp.tool()
async def feature_engineer(
    data_url: str, 
    operations: List[str] = []
) -> str:
    """ENGINEERS features. [ACTION]
    
    [RAG Context]
    Create derived features from existing columns.
    Returns modified data summary.
    """
    return await run_op(cleaning.feature_engineer, data_url=data_url, operations=operations)

# --- 3. Stats & Correlation ---
@mcp.tool()
async def correlation_matrix(
    data_url: str = None, 
    data: Dict[str, Any] = None, 
    method: str = "pearson", 
    threshold: float = 0.0
) -> str:
    """CALCULATES correlations. [ACTION]
    
    [RAG Context]
    Compute correlation matrix for numeric columns.
    Returns correlation table.
    """
    return await run_op(stats.correlation_matrix, data_url=data_url, data=data, method=method, threshold=threshold)

@mcp.tool()
async def statistical_test(
    data_url: str, 
    test_type: str, 
    column1: str = None, 
    column2: str = None, 
    group_column: str = None
) -> str:
    """TESTS statistics. [ACTION]
    
    [RAG Context]
    Run statistical tests on data (ttest, anova, chi2).
    Returns test results.
    """
    return await run_op(stats.statistical_test, data_url=data_url, test_type=test_type, column1=column1, column2=column2, group_column=group_column)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class AnalyticsServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
