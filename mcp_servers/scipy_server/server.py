
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
# from mcp_servers.scipy_server.tools import (
#     stats_ops, opt_ops, integ_ops, signal_ops, linalg_ops, spatial_ops, super_ops,
#     interp_ops, cluster_ops, ndimage_ops, special_ops
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

import warnings
warnings.filterwarnings("ignore", message="One or more sample arguments is too small")
warnings.filterwarnings("ignore", category=RuntimeWarning)

mcp = FastMCP("scipy_server", dependencies=["scipy", "numpy", "pandas"])

# ==========================================
# 0. Core Logic (Implicit in helpers)
# ==========================================

# ==========================================
# 1. Statistics (The Bulk)
# ==========================================
@mcp.tool()
async def describe_data(data: Union[List[float], str]) -> Dict[str, Any]: 
    """CALCULATES professional-grade descriptive statistics for numerical datasets. [DATA]
    
    [RAG Context]
    An elite "Statistical Profiling Super Tool" that serves as the definitive starting point for any rigorous data investigation. Beyond simple averages, this tool computes the fundamental "Four Moments" of a distribution: the Mean (first moment), Variance (second moment), Skewness (third moment/asymmetry), and Kurtosis (fourth moment/tail-weight). These metrics allow the Kea system to instantly determine the "Health" and "Shape" of a data collection. It is the mandatory tool for "Initial Data Auditing," providing the necessary mathematical context to decide which advanced statistical tests or predictive models are appropriate for the data at hand.
    
    How to Use:
    - Input 'data' as a raw list of numbers or a reference string.
    - Check 'Skewness': A value far from 0 indicates an unbalanced distribution where outliers might pull the mean away from the median.
    - Check 'Kurtosis': High values indicate a "Heavy-Tailed" distribution, warning the system of high-impact extreme events.
    
    Keywords: descriptive statistics, statistical moments, skewness analysis, kurtosis audit, data profiling, distribution shape.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.describe_data(data)

@mcp.tool()
async def get_percentiles(data: Union[List[float], str], percentiles: List[float] = [25, 50, 75]) -> Dict[str, float]: 
    """CALCULATES specific value thresholds (Percentiles) for a distribution. [DATA]
    
    [RAG Context]
    A high-precision "Distribution Mapping Super Tool" for technical benchmarking and Service Level Agreement (SLA) verification. While an average provides a single point of reference, percentiles allow the system to map the entire "Economic Ladder" or "Performance Scale" of a dataset. For example, calculating the 90th percentile of 'Query Latency' tells you that 90% of your users experience better performance than that specific value. It is the mandatory tool for "Risk Management" and "Performance Auditing," allowing the agent to define the boundaries of "Normal" vs "Extreme" behavior within a population.
    
    How to Use:
    - 'percentiles': Provide a list of values from 0 to 100.
    - Standard values include 25 (Q1/Lower Quartile), 50 (Median), and 75 (Q3/Upper Quartile).
    - Perfect for identifying the "Top 1%" of earners, the "Bottom 10%" of performing products, or setting "Outlier Thresholds."
    
    Keywords: percentile calculation, distribution mapping, performance benchmarks, quartile analysis, sla auditing, data thresholds.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.get_percentiles(data, percentiles)

@mcp.tool()
async def get_zscore(data: Union[List[float], str]) -> List[float]: 
    """TRANSFORMS raw data into standardized Z-scores for universal comparison. [DATA]
    
    [RAG Context]
    A critical "Standardization Super Tool" used to neutralize the scale of disparate variables. The Z-score (or standard score) calculates exactly how many standard deviations a raw data point is from its sample mean. This is the mandatory first step for "Distance-Based Clustering" and "Multivariate Comparison," where you might need to compare 'Height' in centimeters with 'Weight' in kilograms. By putting both on a Z-score scale (centered at 0 with a unit variance), you ensure that features with naturally larger numbers do not disproportionately dominate the mathematical analysis.
    
    How to Use:
    - Converts a list of numbers into a scale where 0 is exactly average.
    - Values > 3.0 or < -3.0 are statistically significant outliers (the "3-Sigma" rule).
    - Essential for anomaly detection, fraud identification, and preparing competitive ranking datasets.
    
    Keywords: standardization, z-score normalization, data scaling, 3-sigma rule, anomaly detection, feature parity.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.get_zscore(data)

@mcp.tool()
async def get_iqr(data: Union[List[float], str]) -> float: 
    """CALCULATES Interquartile Range. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.get_iqr(data)

@mcp.tool()
async def get_entropy(data: Union[List[float], str]) -> float: 
    """CALCULATES Shannon entropy. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.get_entropy(data)

@mcp.tool()
async def get_mode(data: Union[List[float], str]) -> Dict[str, Any]: 
    """FINDs the mode (most common value). [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.get_mode(data)

# Tests
@mcp.tool()
async def test_normality(data: Union[List[float], str]) -> Dict[str, Any]: 
    """TESTS for normal distribution. [ACTION]
    
    [RAG Context]
    Performs rigorous statistical tests (Shapiro-Wilk) to determine if a sample came from a normally distributed population.
    
    How to Use:
    - If p-value < 0.05: The null hypothesis of normality is rejected (data is NOT normal).
    - If p-value > 0.05: We fail to reject normality (safe to assume Gaussian for most tests).
    
    Keywords: normality check, gaussian test, shapiro-wilk, p-value.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.test_normality(data)

@mcp.tool()
async def ttest_ind(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """PERFORMS a rigorous Independent T-test to compare the means of two distinct groups. [ACTION]
    
    [RAG Context]
    An authoritative "Decision Validation Super Tool" for A/B testing and comparative research. It provides the experimental proof needed to determine if the difference between two groups (e.g., "Sales with Discount" vs "Sales without Discount") is a real, statistically significant phenomenon or just a result of random noise. It calculates a T-statistic and a P-value; if the P-value is below your significance threshold (standard is 0.05), you have "Statistical Evidence" that the groups are actually different. It is the mandatory tool for "Impact Assessment" and verifying the success of corporate interventions.
    
    How to Use:
    - 'data1', 'data2': Two independent lists of numerical observations.
    - Check the 'p-value': If p < 0.05, you can confidently state that the groups differ.
    - Assume internal normality and equal variance for the most accurate results.
    
    Keywords: independent t-test, a/b testing, mean comparison, statistical significance, p-value analysis, experimental validation.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.ttest_ind(data1, data2)

@mcp.tool()
async def ttest_rel(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """PERFORMS T-test (related/paired). [ACTION]
    
    [RAG Context]
    Compares means of two related samples.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.ttest_rel(data1, data2)

@mcp.tool()
async def mannwhitneyu(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """PERFORMS Mann-Whitney U rank test. [ACTION]
    
    [RAG Context]
    Non-parametric alternative to T-test.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.mannwhitneyu(data1, data2)

@mcp.tool()
async def wilcoxon(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """PERFORMS Wilcoxon signed-rank test. [ACTION]
    
    [RAG Context]
    Non-parametric alternative to paired T-test.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.wilcoxon(data1, data2)

@mcp.tool()
async def kruskal(datasets: List[Union[List[float], str]]) -> Dict[str, Any]: 
    """PERFORMS Kruskal-Wallis H-test. [ACTION]
    
    [RAG Context]
    Non-parametric ANOVA.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.kruskal(datasets)

@mcp.tool()
async def anova_oneway(datasets: List[Union[List[float], str]]) -> Dict[str, Any]: 
    """PERFORMS One-way ANOVA. [ACTION]
    
    [RAG Context]
    Tests equality of means across multiple groups.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.anova_oneway(datasets)

@mcp.tool()
async def ks_test(data: Union[List[float], str], cdf: str = 'norm') -> Dict[str, Any]: 
    """PERFORMS Kolmogorov-Smirnov test. [ACTION]
    
    [RAG Context]
    Goodness of fit against a distribution.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.ks_test(data, cdf)

# Correlations
@mcp.tool()
async def pearson_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """CALCULATES the Pearson product-moment correlation coefficient (r) between two variables. [DATA]
    
    [RAG Context]
    A bedrock "Relational Analysis Super Tool" for measuring the linear relationship between two continuous variables. It quantifies how much one variable changes in direct proportion to another. For example, "Does increase in Advertising Spend directly lead to a proportional increase in Sales?" The Pearson coordinate ranges from -1 (perfect negative correlation) to +1 (perfect positive correlation), with 0 indicating no linear relationship at all. It is the mandatory tool for "Predictive Screening," allowing the system to identify which features have the strongest direct influence on a target outcome before building complex regression models.
    
    How to Use:
    - 'data1', 'data2': Two lists of equal length.
    - Result includes the Pearson 'r' and a 'p-value'.
    - A significant p-value (< 0.05) indicates that the observed correlation is unlikely to have occurred by chance.
    - Best used for data that is normally distributed and has a likely linear relationship.
    
    Keywords: pearson correlation, relationship strength, linear association, predictive screening, correlation coefficient, r-value.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.pearson_corr(data1, data2)

@mcp.tool()
async def spearman_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """CALCULATES the Spearman rank-order correlation coefficient (rho) for non-linear relationships. [DATA]
    
    [RAG Context]
    A sophisticated "Non-Parametric Relationship Super Tool" that detects monotonic relationships regardless of their linear shape. Unlike Pearson, Spearman works by ranking the data first, which makes it far more robust to outliers and capable of identifying relationships that "always go up" even if they don't do so at a constant rate (e.g., exponential growth). In the Kea corporate system, this is the preferred tool for "High-Noise Environments" and "Ordinal Data" (like ranking satisfaction scores), providing a more truthful measure of association when the strict assumptions of linear math are violated.
    
    How to Use:
    - Ideal for data that is skewed or contains extreme values that would distort a standard Pearson calculation.
    - Provides a correlation coefficient and a p-value for significance testing.
    - It answers the question: "As Variable A increases, does Variable B consistently increase/decrease, even if the rate of change varies?"
    
    Keywords: spearman correlation, rank correlation, monotonic relationship, robust association, non-parametric test, rho-value.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.spearman_corr(data1, data2)

@mcp.tool()
async def kendall_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: 
    """CALCULATES Kendall's tau. [DATA]
    
    [RAG Context]
    Ordinal association.
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.kendall_corr(data1, data2)

# Fitting
@mcp.tool()
async def fit_norm(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Normal distribution. [ACTION]
    
    [RAG Context]
    Returns loc (mean) and scale (std).
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_norm(data)

@mcp.tool()
async def fit_expon(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Exponential distribution. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_expon(data)

@mcp.tool()
async def fit_gamma(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Gamma distribution. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_gamma(data)

@mcp.tool()
async def fit_beta(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Beta distribution. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_beta(data)

@mcp.tool()
async def fit_lognorm(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Log-Normal distribution. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_lognorm(data)

@mcp.tool()
async def fit_weibull(data: Union[List[float], str]) -> Dict[str, float]: 
    """FITS Weibull distribution. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import stats_ops
    return await stats_ops.fit_weibull(data)


# ==========================================
# 2. Optimization
# ==========================================
@mcp.tool()
async def minimize_scalar(func_str: str, method: str = 'brent') -> Dict[str, Any]: 
    """MINIMIZES a scalar function. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.minimize_scalar(func_str, method)

@mcp.tool()
async def minimize_bfgs(func_str: str, x0: List[float]) -> Dict[str, Any]: 
    """MINIMIZES function using BFGS. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.minimize_bfgs(func_str, x0)

@mcp.tool()
async def minimize_nelder(func_str: str, x0: List[float]) -> Dict[str, Any]: 
    """MINIMIZES function using Nelder-Mead. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.minimize_nelder(func_str, x0)

@mcp.tool()
async def find_root(func_str: str, a: float, b: float) -> float: 
    """FINDS root of scalar function. [ACTION]
    
    [RAG Context]
    Uses Brent's method.
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.find_root(func_str, a, b)

@mcp.tool()
async def curve_fit(func_str: str, x_data: Union[List[float], str], y_data: Union[List[float], str]) -> Dict[str, Any]: 
    """PERFORMS non-linear least squares to fit a custom mathematical function to empirical data points. [ACTION]
    
    [RAG Context]
    An elite "Mathematical Modeling Super Tool" that allows the Kea system to "learn" the specific parameters of a physical or business law. Unlike simple linear regression, 'curve_fit' can optimize any arbitrary function—such as an exponential decay model for radiation, a logistic curve for user growth, or a sinusoidal wave for seasonal sales. It iteratively adjusts the coefficients of your function to minimize the distance between the model and the actual data points. It is the mandatory tool for "Scientific Discovery" and "Custom Forecasting," enabling the system to generate precise mathematical formulas that describe observed reality.
    
    How to Use:
    - 'func_str': A Python lambda or function string (e.g., `'lambda x, a, b, c: a * exp(-b * x) + c'`).
    - Returns 'popt' (the best-fitting parameters) and 'pcov' (the covariance matrix, indicating the uncertainty in those parameters).
    - Crucial for converting raw datasets into actionable, predictive equations.
    
    Keywords: curve fitting, non-linear least squares, parameter optimization, mathematical modeling, custom regression, predictive formula.
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.curve_fit(func_str, x_data, y_data)

@mcp.tool()
async def linear_sum_assignment(cost_matrix: List[List[float]]) -> Dict[str, Any]: 
    """SOLVES linear sum assignment. [ACTION]
    
    [RAG Context]
    Hungarian algorithm.
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.linear_sum_assignment(cost_matrix)

@mcp.tool()
async def linprog(c: List[float], A_ub: List[List[float]] = None, b_ub: List[float] = None, A_eq: List[List[float]] = None, b_eq: List[float] = None, bounds: List[List[float]] = None) -> Dict[str, Any]: 
    """SOLVES complex linear programming problems for optimal resource allocation. [ACTION]
    
    [RAG Context]
    The absolute "Strategic Optimization Super Tool" for corporate resource management and logistical planning. It finds the mathematical "Best Case" (maximum profit or minimum cost) for a scenario with multiple variables and complex constraints. For example, "How should we allocate our $1M marketing budget across 5 channels to maximize lead conversion while ensuring each channel gets at least $50k but no more than $500k?" This tool converts these business dilemmas into a global optimization problem, providing the mathematically optimal solution that a human alone could never calculate.
    
    How to Use:
    - 'c': The objective function coefficients (what you want to minimize/maximize).
    - 'A_ub', 'b_ub': The inequality constraints (e.g., "Budget <= Total").
    - 'A_eq', 'b_eq': The equality constraints (e.g., "Total Hours == 40").
    - Essential for supply chain management, financial portfolio balancing, and workforce scheduling.
    
    Keywords: linear programming, linprog, strategic optimization, resource allocation, simplex method, constrained best-case.
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.linprog(c, A_ub, b_ub, A_eq, b_eq, bounds)

# Global
@mcp.tool()
async def basinhopping(func_str: str, x0: List[float], niter: int = 100) -> Dict[str, Any]: 
    """FINDS global minimum (Basinhopping). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.basinhopping(func_str, x0, niter)

@mcp.tool()
async def differential_evolution(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]: 
    """FINDS global minimum (Diff Evol). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.differential_evolution(func_str, bounds)

@mcp.tool()
async def dual_annealing(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]: 
    """FINDS global minimum (Dual Annealing). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import opt_ops
    return await opt_ops.dual_annealing(func_str, bounds)


# ==========================================
# 3. Integration
# ==========================================
@mcp.tool()
async def integrate_quad(func_str: str, a: float, b: float) -> Dict[str, float]: 
    """INTEGRATES function (definite). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import integ_ops
    return await integ_ops.integrate_quad(func_str, a, b)

@mcp.tool()
async def integrate_simpson(y_data: Union[List[float], str], x_data: Optional[Union[List[float], str]] = None, dx: float = 1.0) -> float: 
    """INTEGRATES samples (Simpson's rule). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import integ_ops
    return await integ_ops.integrate_simpson(y_data, x_data, dx)

@mcp.tool()
async def integrate_trapezoid(y_data: Union[List[float], str], x_data: Optional[Union[List[float], str]] = None, dx: float = 1.0) -> float: 
    """INTEGRATES samples (Trapezoidal rule). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import integ_ops
    return await integ_ops.integrate_trapezoid(y_data, x_data, dx)

@mcp.tool()
async def solve_ivp(func_str: str, t_span: List[float], y0: List[float], t_eval: List[float] = None) -> Dict[str, Any]: 
    """SOLVES Initial Value Problem (ODE). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import integ_ops
    return await integ_ops.solve_ivp(func_str, t_span, y0, t_eval)


# ==========================================
# 4. Signal Processing
# ==========================================
@mcp.tool()
async def find_peaks(data: Union[List[float], str], height: Optional[float] = None, distance: Optional[int] = None) -> Dict[str, Any]: 
    """IDENTIFIES significant local maxima (peaks) within a 1D signal or time-series. [DATA]
    
    [RAG Context]
    A high-performance "Event Discovery Super Tool" for signal processing and telemetry analysis. In many real-world datasets—such as sensor logs, heartbeat monitors, or stock market volatility—the most important information is often concentrated in the sudden "Spikes" rather than the average values. This tool scans the data to locate these peaks based on specified quantitative criteria. It is the mandatory tool for "Anomaly Detection" and "Rhythmic Analysis," allowing the system to automatically identify significant historical events, system alerts, or recurring patterns in a continuous stream of data.
    
    How to Use:
    - 'height': Set a minimum vertical threshold to ignore background noise and small ripples.
    - 'distance': Set a minimum horizontal gap to prevent multiple detections of the same broad event.
    - Result includes the precise indices and properties of all discovered peaks, enabling rapid focused analysis on those specific time points.
    
    Keywords: spike detection, local maxima, peak finding, event identification, signal anomalies, telemetry spikes.
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.find_peaks(data, height, distance)

@mcp.tool()
async def fft(data: Union[List[float], str]) -> Dict[str, Any]: 
    """COMPUTES FFT of signal. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.compute_fft(data)

@mcp.tool()
async def ifft(data_real: Union[List[float], str], data_imag: Optional[Union[List[float], str]] = None) -> List[float]: 
    """COMPUTES Inverse FFT. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.compute_ifft(data_real, data_imag)

@mcp.tool()
async def resample(data: Union[List[float], str], num: int) -> List[float]: 
    """RESAMPLES signal to new length. [ACTION]
    
    [RAG Context]
    Fourier method.
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.resample(data, num)

@mcp.tool()
async def medfilt(data: Union[List[float], str], kernel_size: int = 3) -> List[float]: 
    """APPLIES median filter. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.medfilt(data, kernel_size)

@mcp.tool()
async def wiener(data: Union[List[float], str]) -> List[float]: 
    """APPLIES Wiener filter. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.wiener(data)

@mcp.tool()
async def savgol_filter(data: Union[List[float], str], window_length: int = 5, polyorder: int = 2) -> List[float]: 
    """APPLIES Savitzky-Golay filter. [ACTION]
    
    [RAG Context]
    Smoothing.
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.savgol_filter(data, window_length, polyorder)

@mcp.tool()
async def detrend(data: Union[List[float], str], type: str = 'linear') -> List[float]: 
    """REMOVES linear trend. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import signal_ops
    return await signal_ops.detrend(data, type)


# ==========================================
# 5. Linear Algebra
# ==========================================
@mcp.tool()
async def matrix_inv(matrix: List[List[float]]) -> List[List[float]]: 
    """COMPUTES matrix inverse. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.matrix_inv(matrix)

@mcp.tool()
async def matrix_det(matrix: List[List[float]]) -> float: 
    """CALCULATES determinant. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.matrix_det(matrix)

@mcp.tool()
async def matrix_norm(matrix: List[List[float]], ord: str = None) -> float: 
    """CALCULATES matrix norm. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.matrix_norm(matrix, ord)

@mcp.tool()
async def solve_linear(a: List[List[float]], b: List[float]) -> List[float]: 
    """SOLVES linear equation Ax = b. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.solve_linear(a, b)

@mcp.tool()
async def svd_decomp(matrix: List[List[float]]) -> Dict[str, Any]: 
    """COMPUTES the Singular Value Decomposition (SVD) for matrix factorizaton and data compression. [ACTION]
    
    [RAG Context]
    An elite "Mathematical Foundation Super Tool" that decomposes any matrix into three constituent parts (U, Sigma, and V). SVD is the theoretical engine behind almost all modern data science: from "High-Dimensional Data Compression" and "Image De-noising" to "Principal Component Analysis" and "Latent Semantic Analysis." It effectively reveals the hidden "Structure" and "Rank" of a dataset by identifying the most significant directions of variance. It is the mandatory tool for "Dimensionality Reduction," allowing the Kea system to simplify massive datasets while preserving their most critical relational information.
    
    How to Use:
    - Transforms a complex matrix into a set of "Singular Values" that indicate how much information is contained in each dimension.
    - Used to found the "Numerical Rank" of a matrix, identifying if certain variables are redundant or purely noise.
    - Essential for sophisticated recommendation systems and solving "Ill-Conditioned" linear systems.
    
    Keywords: svd decomposition, matrix factorization, data compression, latent feature discovery, rank analysis, dimensionality reduction.
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.svd_decomp(matrix)

@mcp.tool()
async def eig_decomp(matrix: List[List[float]]) -> Dict[str, Any]: 
    """COMPUTES eigenvalues/vectors. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.eig_decomp(matrix)

@mcp.tool()
async def lu_factor(matrix: List[List[float]]) -> Dict[str, Any]: 
    """COMPUTES LU factorization. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.lu_factor(matrix)

@mcp.tool()
async def cholesky(matrix: List[List[float]]) -> List[List[float]]: 
    """COMPUTES Cholesky decomposition. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import linalg_ops
    return await linalg_ops.cholesky(matrix)


# ==========================================
# 6. Spatial
# ==========================================
@mcp.tool()
async def distance_euclidean(u: List[float], v: List[float]) -> float: 
    """CALCULATES the straight-line (Euclidean) distance between two multi-dimensional points. [DATA]
    
    [RAG Context]
    A fundamental "Spatial Relationship Super Tool" that measures the absolute "Physical" distance between two data vectors in an N-dimensional space. It is the standard metric for "Similarity Analysis"—the closer two items are in Euclidean space, the more similar they are across all compared features. This tool is the core building block for "Nearest Neighbor" algorithms, "Constraint Satisfaction" in robotics, and for calculating the true magnitude of difference between two disparate observations (e.g., comparing a "Standard User Profile" with a "New Session Profile" to detect behavioral drift).
    
    How to Use:
    - 'u', 'v': Two lists of numbers representing coordinates (or feature vectors).
    - Returns a single positive float; 0.0 indicates identity.
    - Standard choice for when the physical magnitude of the difference in each dimension is equally important.
    
    Keywords: euclidean distance, l2 norm, similarity metric, spatial analysis, proximity check, vector distance.
    """
    from mcp_servers.scipy_server.tools import spatial_ops
    return await spatial_ops.distance_euclidean(u, v)

@mcp.tool()
async def distance_cosine(u: List[float], v: List[float]) -> float: 
    """CALCULATES Cosine distance. [DATA]
    
    [RAG Context]
    1 - cosine similarity.
    """
    from mcp_servers.scipy_server.tools import spatial_ops
    return await spatial_ops.distance_cosine(u, v)

@mcp.tool()
async def distance_matrix(x: List[List[float]], y: List[List[float]]) -> List[List[float]]: 
    """COMPUTES distance matrix. [DATA]
    
    [RAG Context]
    Pairwise distances.
    """
    from mcp_servers.scipy_server.tools import spatial_ops
    return await spatial_ops.distance_matrix(x, y)

@mcp.tool()
async def convex_hull(points: List[List[float]]) -> Dict[str, Any]: 
    """COMPUTES Convex Hull. [ACTION]
    
    [RAG Context]
    Smallest convex set containing points.
    """
    from mcp_servers.scipy_server.tools import spatial_ops
    return await spatial_ops.convex_hull(points)


# ==========================================
# 7. Super Tools
# ==========================================
@mcp.tool()
async def analyze_distribution(data: List[float]) -> Dict[str, Any]: 
    """PERFORMS an exhaustive automated search to find the best-fitting probability distribution for a dataset. [ENTRY]
    
    [RAG Context]
    The ultimate "Stochastic Discovery Super Tool" for industrial-grade data modeling. In professional statistical analysis, assuming that data is "Normal" is a common but often dangerous mistake. This tool uses SciPy's extensive library to attempt fitting over 80 different continuous probability distributions (including Gamma, Beta, Weibull, and Cauchy) to your raw data. It ranks them objectively using the "Sum of Square Errors" (SSE) or a similar goodness-of-fit metric. It is the mandatory tool for "Scientific Modeling" and "Risk Assessment," allowing the system to discover the true physical or economic law governing the data—critical for calculating accurate failure rates, insurance premiums, or future predictions.
    
    How to Use:
    - Simply provide a list of numeric observations.
    - Result includes the top-ranked distributions along with their optimized parameters (loc, scale, and shape).
    - Use this before generating synthetic data or performing Monte Carlo simulations to ensure your "World Model" matches reality.
    
    Keywords: distribution fitting, stochastic discovery, best-fit analysis, probability modeling, scientific data audit, goodness of fit.
    """
    from mcp_servers.scipy_server.tools import super_ops
    return await super_ops.analyze_distribution(data)

@mcp.tool()
async def signal_dashboard(data: List[float]) -> Dict[str, Any]: 
    """GENERATES signal analysis dashboard. [ENTRY]
    
    [RAG Context]
    A comprehensive "Super Tool" for analyzing time-varying signals. Combines statistical moments, spectral decomposition (FFT), and peak detection into a single results object.
    
    Keywords: signal overview, spectrogram info, spike analysis, frequency profile.
    """
    from mcp_servers.scipy_server.tools import super_ops
    return await super_ops.signal_dashboard(data)

@mcp.tool()
async def compare_samples(sample1: List[float], sample2: List[float]) -> Dict[str, Any]: 
    """COMPARES two samples. [ENTRY]
    
    [RAG Context]
    Statistical tests (T-test, KS, etc).
    """
    from mcp_servers.scipy_server.tools import super_ops
    return await super_ops.compare_samples(sample1, sample2)

# ==========================================
# 8. Interpolation (Ultimate)
# ==========================================
@mcp.tool()
async def interp_1d(x: Union[List[float], str], y: Union[List[float], str], x_new: Union[List[float], str], kind: str = 'linear') -> List[float]: 
    """INTERPOLATES 1-D function. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import interp_ops
    return await interp_ops.interp_1d(x, y, x_new, kind)

@mcp.tool()
async def interp_spline(x: Union[List[float], str], y: Union[List[float], str], x_new: Union[List[float], str], k: int = 3, s: float = 0) -> List[float]: 
    """INTERPOLATES using B-splines. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import interp_ops
    return await interp_ops.interp_spline(x, y, x_new, k, s)

@mcp.tool()
async def grid_data(points: List[List[float]], values: Union[List[float], str], xi: List[List[float]], method: str = 'linear') -> List[float]: 
    """INTERPOLATES unstructured data. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import interp_ops
    return await interp_ops.grid_data(points, values, xi, method)

# ==========================================
# 9. Clustering (Ultimate)
# ==========================================
@mcp.tool()
async def kmeans(data: List[List[float]], k_or_guess: Any) -> Dict[str, Any]: 
    """PERFORMS high-speed K-Means vector quantization to identify natural clusters in multi-dimensional data. [ACTION]
    
    [RAG Context]
    A foundational "Unsupervised Learning Super Tool" for pattern recognition and demographic segmentation. It mathematically partitions a large set of points into 'K' distinct clusters based on their proximity to a central "Centroid." In the Kea corporate system, this is the primary tool for "Customer Archetyping" (grouping users with similar behaviors) and "Image Compression" (reducing a full-color image to a palette of 'K' dominant colors). It effectively turns unstructured, chaotic scatter-data into clear, manageable groupings that represent the internal "Themes" of the dataset.
    
    How to Use:
    - 'k_or_guess': Either the specific number of clusters desired or an initial guess for the centroid positions.
    - Data should be standardized (using 'get_zscore' or 'whitening') before clustering to ensure each dimension contributes equally to the distance calculation.
    - Perfect for initializing "Target Audits" and identifying the representative "Center Points" of complex behaviors.
    
    Keywords: k-means clustering, vector quantization, unsupervised pattern discovery, centroid analysis, segment identification, grouping algorithm.
    """
    from mcp_servers.scipy_server.tools import cluster_ops
    return await cluster_ops.kmeans(data, k_or_guess)

@mcp.tool()
async def whitening(data: List[List[float]]) -> List[List[float]]: 
    """WHITENS data (unit variance). [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import cluster_ops
    return await cluster_ops.whitening(data)

@mcp.tool()
async def linkage_matrix(data: List[List[float]], method: str = 'single', metric: str = 'euclidean') -> List[List[float]]: 
    """COMPUTES operations hierarchical clustering linkage. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import cluster_ops
    return await cluster_ops.linkage_matrix(data, method, metric)

@mcp.tool()
async def fcluster(Z: List[List[float]], t: float, criterion: str = 'distance') -> List[int]: 
    """FORMS flat clusters from linkage. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import cluster_ops
    return await cluster_ops.fcluster(Z, t, criterion)

# ==========================================
# 10. ND-Image (Ultimate)
# ==========================================
@mcp.tool()
async def img_gaussian(data: List[List[float]], sigma: float) -> List[List[float]]: 
    """APPLIES a multi-dimensional Gaussian blur to smooth data or denoise images. [ACTION]
    
    [RAG Context]
    A sophisticated "Signal Smoothing Super Tool" used to reduce high-frequency noise and soften the transitions in a matrix or image. Gaussian filtering works by "convolving" each point with a bell-curve weight, ensuring that the local average is weighted most strongly at the center. This is the mandatory tool for "Scientific Noise Reduction" and "Image Preprocessing," providing a clean, smoothed baseline that improves the accuracy of subsequent operations like edge detection or object recognition. It is the numerical equivalent of looking at data "through a soft lens" to see the broad trends rather than the pixel-level jitter.
    
    How to Use:
    - 'sigma': The standard deviation of the Gaussian kernel; higher values result in a more intense blur.
    - Essential for removing "Salt and Pepper" noise in visual data or for creating "Heatmap" effects in 2D density plots.
    
    Keywords: gaussian blur, image smoothing, signal denoising, convolution filter, bell-curve smoothing, data softening.
    """
    from mcp_servers.scipy_server.tools import ndimage_ops
    return await ndimage_ops.img_gaussian(data, sigma)

@mcp.tool()
async def img_sobel(data: List[List[float]], axis: int = -1) -> List[List[float]]: 
    """CALCULATES Sobel edge filter. [ACTION]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import ndimage_ops
    return await ndimage_ops.img_sobel(data, axis)

@mcp.tool()
async def img_laplace(data: List[List[float]]) -> List[List[float]]: 
    """CALCULATES Laplace filter. [ACTION]
    
    [RAG Context]
    Edge detection.
    """
    from mcp_servers.scipy_server.tools import ndimage_ops
    return await ndimage_ops.img_laplace(data)

@mcp.tool()
async def img_median(data: List[List[float]], size: int = 3) -> List[List[float]]: 
    """APPLIES median filter to image. [ACTION]
    
    [RAG Context]
    Noise removal.
    """
    from mcp_servers.scipy_server.tools import ndimage_ops
    return await ndimage_ops.img_median(data, size)

@mcp.tool()
async def center_of_mass(data: List[List[float]]) -> List[float]: 
    """CALCULATES center of mass. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import ndimage_ops
    return await ndimage_ops.center_of_mass(data)

# ==========================================
# 11. Special Functions (Ultimate)
# ==========================================
@mcp.tool()
async def gamma_func(z: Union[List[float], str]) -> List[float]: 
    """CALCULATES Gamma function. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import special_ops
    return await special_ops.gamma_func(z)

@mcp.tool()
async def beta_func(a: Union[List[float], str], b: Union[List[float], str]) -> List[float]: 
    """CALCULATES Beta function. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import special_ops
    return await special_ops.beta_func(a, b)

@mcp.tool()
async def erf_func(z: Union[List[float], str]) -> List[float]: 
    """CALCULATES Error function. [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import special_ops
    return await special_ops.erf_func(z)

@mcp.tool()
async def bessel_j0(z: Union[List[float], str]) -> List[float]: 
    """CALCULATES Bessel function (order 0). [DATA]
    
    [RAG Context]
    """
    from mcp_servers.scipy_server.tools import special_ops
    return await special_ops.bessel_j0(z)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class ScipyServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

