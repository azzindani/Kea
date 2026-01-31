# /// script
# dependencies = [
#   "mcp",
#   "numpy",
#   "pandas",
#   "scipy",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import eda, cleaning, stats
import structlog
import asyncio
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
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
    """
    Perform automatic Exploratory Data Analysis.
    data_url: URL/path to CSV
    data: Inline data {columns: [], rows: []}
    """
    return await run_op(eda.eda_auto, data_url=data_url, data=data, target_column=target_column)

@mcp.tool()
async def data_profiler(
    data_url: str, 
    minimal: bool = True
) -> str:
    """Generate detailed data profile report."""
    return await run_op(eda.data_profiler, data_url=data_url, minimal=minimal)

# --- 2. Cleaning & Feature Engineering ---
@mcp.tool()
async def data_cleaner(
    data_url: str,
    handle_missing: str = "none",
    handle_outliers: str = "none",
    remove_duplicates: bool = False
) -> str:
    """
    Clean dataset: handle missing values, outliers, duplicates.
    handle_missing: drop, mean, median, mode, ffill
    handle_outliers: none, clip, drop
    """
    return await run_op(cleaning.data_cleaner, data_url=data_url, handle_missing=handle_missing, handle_outliers=handle_outliers, remove_duplicates=remove_duplicates)

@mcp.tool()
async def feature_engineer(
    data_url: str, 
    operations: List[str] = []
) -> str:
    """
    Create derived features from existing columns.
    operations: list of operation strings
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
    """
    Compute correlation matrix for numeric columns.
    method: pearson, spearman, kendall
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
    """
    Run statistical tests on data.
    test_type: ttest, anova, chi2, normality
    """
    return await run_op(stats.statistical_test, data_url=data_url, test_type=test_type, column1=column1, column2=column2, group_column=group_col)

if __name__ == "__main__":
    mcp.run()