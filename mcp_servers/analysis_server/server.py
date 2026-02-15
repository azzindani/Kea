
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

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.analysis_server.tools import stats_ops
import structlog
from typing import List, Dict, Any, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.structured import setup_logging
setup_logging()



mcp = FastMCP("analysis_server", dependencies=["pandas", "numpy", "scikit-learn", "xgboost", "tensorflow", "matplotlib", "seaborn", "statsmodels", "scipy"])

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

@mcp.tool()
async def analyze_data_science_project(dataset_url: str, target_column: str, goal: str) -> Dict[str, Any]:
    """EXECUTES end-to-end DS project. [ACTION]
    
    [RAG Context]
    "Multitalent" Agent that orchestrates cleaning, profiling, and modeling (ML/DL).
    Inputs: dataset_url, target_column, goal.
    """
    from mcp_servers.analysis_server.tools import agent_ops
    return await agent_ops.analyze_data_science_project(dataset_url, target_column, goal)


# ==========================================
# 3. Visualization Tools (New)
# ==========================================
# ==========================================
# 3. Visualization Tools (New)
# ==========================================
@mcp.tool()
def plot_scatter(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "scatter.png") -> str:
    """PLOTS Scatter chart. [ACTION]
    
    [RAG Context]
    XY scatter plot for correlation.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_scatter(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_line(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "line.png") -> str:
    """PLOTS Line chart. [ACTION]
    
    [RAG Context]
    Time-series or sequential data plot.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_line(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_bar(file_path: str, x: str, y: str, hue: Optional[str] = None, output_path: str = "bar.png") -> str:
    """PLOTS Bar chart. [ACTION]
    
    [RAG Context]
    Categorical comparison.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_bar(file_path, x, y, hue, output_path)

@mcp.tool()
def plot_hist(file_path: str, x: str, bins: int = 20, hue: Optional[str] = None, output_path: str = "hist.png") -> str:
    """PLOTS Histogram/Distribution. [ACTION]
    
    [RAG Context]
    Shows frequency distribution.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_hist(file_path, x, bins, hue, output_path)

@mcp.tool()
def plot_box(file_path: str, x: str, y: str, output_path: str = "box.png") -> str:
    """PLOTS Box plot. [ACTION]
    
    [RAG Context]
    Statistical summary (quartiles, outliers).
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_box(file_path, x, y, output_path)

@mcp.tool()
def plot_violin(file_path: str, x: str, y: str, output_path: str = "violin.png") -> str:
    """PLOTS Violin plot. [ACTION]
    
    [RAG Context]
    Distribution + Box plot.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_violin(file_path, x, y, output_path)

@mcp.tool()
def plot_heatmap(file_path: str, output_path: str = "heatmap.png") -> str:
    """PLOTS Correlation Heatmap. [ACTION]
    
    [RAG Context]
    Correlation matrix visualization.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_heatmap(file_path, output_path)

@mcp.tool()
def plot_pairplot(file_path: str, hue: Optional[str] = None, output_path: str = "pairplot.png") -> str:
    """PLOTS Pairplot (Scatter matrix). [ACTION]
    
    [RAG Context]
    Matrix of scatter plots for all features.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_pairplot(file_path, hue, output_path)

@mcp.tool()
def plot_confusion_matrix(file_path: str, y_true: str, y_pred: str, output_path: str="cm.png") -> str:
    """PLOTS Confusion Matrix. [ACTION]
    
    [RAG Context]
    True vs Predicted labels heatmap.
    """
    from mcp_servers.analysis_server.tools import plot_ops
    return plot_ops.plot_confusion_matrix(file_path, y_true, y_pred, output_path)

if __name__ == "__main__":
    mcp.run()


# ==========================================
# 4. Statistical Tests (New)
# ==========================================
@mcp.tool()
def test_ttest_1samp(file_path: str, column: str, population_mean: float) -> Dict[str, Any]:
    """PERFORMS One-Sample T-Test. [DATA]
    
    [RAG Context]
    Compares mean to population mean.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_ttest_1samp(file_path, column, population_mean)

@mcp.tool()
def test_ttest_ind(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Independent T-Test. [DATA]
    
    [RAG Context]
    Compares means of two independent groups.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_ttest_ind(file_path1, col1, file_path2, col2)

@mcp.tool()
def test_mannwhitneyu(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Mann-Whitney U Test. [DATA]
    
    [RAG Context]
    Non-parametric comparison of two groups.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_mannwhitneyu(file_path1, col1, file_path2, col2)

@mcp.tool()
def test_pearsonr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Pearson Correlation. [DATA]
    
    [RAG Context]
    Linear correlation coefficient.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_pearsonr(file_path, col1, col2)

@mcp.tool()
def test_spearmanr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Spearman Correlation. [DATA]
    
    [RAG Context]
    Rank correlation coefficient.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_spearmanr(file_path, col1, col2)

@mcp.tool()
def test_shapiro(file_path: str, column: str) -> Dict[str, Any]:
    """PERFORMS Shapiro-Wilk Normality Test. [DATA]
    
    [RAG Context]
    Tests if data is Gaussian.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_shapiro(file_path, column)

@mcp.tool()
def test_chi2_contingency(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Chi-Square Test. [DATA]
    
    [RAG Context]
    Test of independence for categorical vars.
    """
    from mcp_servers.analysis_server.tools import stat_tests
    return stat_tests.test_chi2_contingency(file_path, col1, col2)

# ==========================================
# 5. Time Series Analysis (New)
# ==========================================
@mcp.tool()
def model_ols_regression(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS OLS Linear Regression. [DATA]
    
    [RAG Context]
    Formula-style regression (e.g. 'y ~ x + z').
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.model_ols_regression(file_path, formula)

@mcp.tool()
def model_arima(file_path: str, value_col: str, order: List[int], date_col: str = None) -> Dict[str, Any]:
    """RUNS ARIMA Model. [DATA]
    
    [RAG Context]
    AutoRegressive Integrated Moving Average.
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.model_arima(file_path, value_col, order, date_col)

@mcp.tool()
def test_adfuller(file_path: str, value_col: str) -> Dict[str, Any]:
    """PERFORMS Augmented Dickey-Fuller Test. [DATA]
    
    [RAG Context]
    Tests for stationarity in time series.
    """
    from mcp_servers.analysis_server.tools import time_series_ops
    return time_series_ops.test_adfuller(file_path, value_col)

# ==========================================
# 8. Advanced Visualizations (New)
# ==========================================
@mcp.tool()
def plot_kde(file_path: str, x: str) -> str:
    """PLOTS KDE Density. [ACTION]
    
    [RAG Context]
    Kernel Density Estimation.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_kde(file_path, x)

@mcp.tool()
def plot_joint(file_path: str, x: str, y: str, kind: str = "scatter") -> str:
    """PLOTS Joint Plot. [ACTION]
    
    [RAG Context]
    Bivariate plot with marginals.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_joint(file_path, x, y, kind)

@mcp.tool()
def plot_3d_scatter(file_path: str, x: str, y: str, z: str) -> str:
    """PLOTS 3D Scatter. [ACTION]
    
    [RAG Context]
    Three-dimensional scatter plot.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_3d_scatter(file_path, x, y, z)

@mcp.tool()
def plot_hexbin(file_path: str, x: str, y: str) -> str:
    """PLOTS Hexbin Plot. [ACTION]
    
    [RAG Context]
    Bivariate histogram with hexagonal bins.
    """
    from mcp_servers.analysis_server.tools import advanced_plot_ops
    return advanced_plot_ops.plot_hexbin(file_path, x, y)

# ==========================================
# 9. Advanced Statistics (New)
# ==========================================
@mcp.tool()
def stat_anova_oneway(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS One-Way ANOVA. [DATA]
    
    [RAG Context]
    Analysis of Variance.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_anova_oneway(file_path, formula)

@mcp.tool()
def stat_logit(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS Logistic Regression. [DATA]
    
    [RAG Context]
    Logit model for binary outcomes.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_logit(file_path, formula)

@mcp.tool()
def stat_glm(file_path: str, formula: str, family: str = 'Gaussian') -> Dict[str, Any]:
    """RUNS GLM. [DATA]
    
    [RAG Context]
    Generalized Linear Model.
    """
    from mcp_servers.analysis_server.tools import advanced_stats_ops
    return advanced_stats_ops.stat_glm(file_path, formula)

# ==========================================
# 10. Signal Processing (New)
# ==========================================
@mcp.tool()
def signal_fft(file_path: str, column: str) -> Dict[str, Any]:
    """COMPUTES FFT. [DATA]
    
    [RAG Context]
    Fast Fourier Transform.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_fft(file_path, column)

@mcp.tool()
def signal_detrend(file_path: str, column: str) -> str:
    """REMOVES linear trend. [ACTION]
    
    [RAG Context]
    Signal detrending.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_detrend(file_path, column)

@mcp.tool()
def signal_resample(file_path: str, column: str, num_samples: int) -> str:
    """RESAMPLES signal. [ACTION]
    
    [RAG Context]
    Changes sampling rate of signal.
    """
    from mcp_servers.analysis_server.tools import signal_ops
    return signal_ops.signal_resample(file_path, column, num_samples)

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
