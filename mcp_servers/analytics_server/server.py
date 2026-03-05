
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
setup_logging(force_stderr=True)

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
    """PERFORMS a high-speed, automated Exploratory Data Analysis (EDA) on a target dataset. [ACTION] [SUPER TOOL]
    
    [RAG Context]
    The absolute "Discovery Phase Super Tool" for any data-driven project. This tool acts as the "Intelligence Scout," scanning raw datasets to automatically identify data types, detect skewed distributions, calculate initial correlations, and flag obvious quality issues. In the Kea corporate kernel, it is the mandatory first step before building any model or drafting any report. It converts "Raw Data" into "Insights," allowing the agent to understand the "Statistical Landscape" and identify potential pitfalls or opportunities for deeper analysis.
    
    How to Use:
    - 'data_url': The path to a CSV or Parquet file.
    - 'target_column': If specified, the tool will prioritize finding relationships that influence this specific metric, identifying key drivers and potential predictors.
    - Returns a comprehensive text summary of the dataset's shape, feature importance, and outlier density.
    
    Keywords: auto eda, dataset profile, initial scan, discovery phase, statistical scouting, data overview.
    """
    return await run_op(eda.eda_auto, data_url=data_url, data=data, target_column=target_column)

@mcp.tool()
async def data_profiler(
    data_url: str, 
    minimal: bool = True
) -> str:
    """GENERATES a deep-dive, technical "Data Profile Report" for a dataset. [ACTION]
    
    [RAG Context]
    An elite "Dataset Audit Super Tool" powered by industry-standard profiling logic. While `eda_auto` provides high-level insights, `data_profiler` creates an exhaustive, variable-by-variable breakdown. It calculates missingness, distinctness, monotonicity, and identifies common data pathologies like "High Correlation" or "Constant Values." It is the mandatory tool for "Pre-Flight Data Verification," ensuring that a dataset is structurally sound and mathematically clean before being ingested into critical enterprise dashboards or machine learning trainers.
    
    How to Use:
    - 'data_url': Path to the remote or local data source.
    - 'minimal': If True (default), it creates a fast summary. If False, it performs a much more intensive analysis, including interaction matrices and detailed histograms for every column.
    
    Keywords: data profiling, dataset audit, structural integrity, technical report, pre-flight check, variable breakdown.
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
    """EXECUTES professional-grade data scrubbing and sanitization procedures. [ACTION] [SUPER TOOL]
    
    [RAG Context]
    The definitive "Scrubbing Super Tool" for corporate data hygiene. Raw enterprise data is almost always "Dirty"—containing missing fields, duplicate entries, and extreme outliers that can corrupt mathematical analysis. This tool provides an automated, multi-tier cleaning pipeline to rectify these issues. It is the mandatory tool for "Reliability Assurance," ensuring that every downstream tool in the Kea system receives a consistent, sanitized, and high-fidelity dataset.
    
    How to Use:
    - 'handle_missing': Specify the strategy ('mean', 'median', 'mode' for imputation, or 'drop' to remove empty rows).
    - 'handle_outliers': Use 'z-score' for Gaussian-based removal or 'iqr' for robust median-based removal.
    - 'remove_duplicates': Set to True to ensure every record in the dataset is unique.
    - Returns a summary of the operations performed and the final health of the cleaned dataset.
    
    Keywords: data cleaning, dataset scrubbing, outlier removal, missing value imputation, deduplication, reliability assurance.
    """
    return await run_op(cleaning.data_cleaner, data_url=data_url, handle_missing=handle_missing, handle_outliers=handle_outliers, remove_duplicates=remove_duplicates)

@mcp.tool()
async def feature_engineer(
    data_url: str, 
    operations: List[str] = []
) -> str:
    """TRANSFORMS raw columns into high-value predictive features. [ACTION]
    
    [RAG Context]
    An elite "Feature Synthesis Super Tool" used to extract the maximum amount of "Predictive Power" from a dataset. In machine learning, the "Raw" data (like 'Purchase Date') is often less useful than a "Synthesized" feature (like 'Days Since Last Purchase'). This tool automates the creation of these higher-order columns through mathematical operations, categorical encoding, and interaction generation. It is the mandatory tool for "Performance Boosting," allowing the Kea system to refine the data for 10x better model accuracy.
    
    How to Use:
    - 'operations': A list of desired transformations (e.g., 'one_hot_encode', 'log_transform', 'delta_creation').
    - Result includes a summary of the new feature landscape and its expected contribution to predictive model strength.
    
    Keywords: feature engineering, variable synthesis, predictive power, data transformation, encoding, performance boost.
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
    """CALCULATES a comprehensive correlation matrix across all numerical variables in a dataset. [ACTION]
    
    [RAG Context]
    A vital "Relational Mapping Super Tool" for identifying the inter-dependencies between disparate business metrics. By calculating the correlation between every pair of columns, the tool reveals "Hidden Redundancies" and "Strategic Lever" relationships (e.g., how strongly 'Social Media Reach' actually correlates with 'Conversion Rate'). It is the mandatory tool for "Feature Selection" and "Relationship Auditing," providing the blueprint for building any multi-variable model.
    
    How to Use:
    - 'method': Use 'pearson' for linear relationships or 'spearman' for more robust, non-linear monotonic associations.
    - 'threshold': Filter out weak correlations to focus only on significant business relationships (e.g., set to 0.7 for strong links only).
    
    Keywords: correlation matrix, relationship mapping, feature selection, dependency audit, business drivers, statistical inter-links.
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
    """PERFORMS rigorous hypothesis testing to provide mathematical proof for business claims. [ACTION]
    
    [RAG Context]
    The definitive "Decision Validation Super Tool" for technical auditing. It moves past simple intuition to provide "Statistical Proof" for observations (e.g., "Is the 5% higher conversion in Region A actually significant, or just a random fluke?"). It supports multiple test types including T-Tests for group comparison, ANOVA for multi-group benchmarking, and Chi-Square for categorical independence. It is the mandatory tool for "Validation Scrutiny," ensuring that every corporate decision is backed by a verifiable P-value.
    
    How to Use:
    - 'test_type': Choose 'ttest', 'anova', or 'chi2'.
    - 'column1', 'column2': The variables you wish to compare.
    - Result includes the test statistic and the P-value; a P-value < 0.05 is the standard threshold for "Statistically Significant" proof.
    
    Keywords: statistical testing, hypothesis validation, ttest, anova, chi2, decision proof, p-value audit.
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

