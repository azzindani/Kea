from mcp.server.fastmcp import FastMCP
from mcp_servers.scipy_server.tools import (
    stats_ops, opt_ops, integ_ops, signal_ops, linalg_ops, spatial_ops, super_ops,
    interp_ops, cluster_ops, ndimage_ops, special_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("scipy_server", dependencies=["scipy", "numpy", "pandas"])

# ==========================================
# 0. Core Logic (Implicit in helpers)
# ==========================================

# ==========================================
# 1. Statistics (The Bulk)
# ==========================================
@mcp.tool()
async def describe_data(data: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.describe_data(data)
@mcp.tool()
async def get_percentiles(data: Union[List[float], str], percentiles: List[float] = [25, 50, 75]) -> Dict[str, float]: return await stats_ops.get_percentiles(data, percentiles)
@mcp.tool()
async def get_zscore(data: Union[List[float], str]) -> List[float]: return await stats_ops.get_zscore(data)
@mcp.tool()
async def get_iqr(data: Union[List[float], str]) -> float: return await stats_ops.get_iqr(data)
@mcp.tool()
async def get_entropy(data: Union[List[float], str]) -> float: return await stats_ops.get_entropy(data)
@mcp.tool()
async def get_mode(data: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.get_mode(data)

# Tests
@mcp.tool()
async def test_normality(data: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.test_normality(data)
@mcp.tool()
async def ttest_ind(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.ttest_ind(data1, data2)
@mcp.tool()
async def ttest_rel(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.ttest_rel(data1, data2)
@mcp.tool()
async def mannwhitneyu(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.mannwhitneyu(data1, data2)
@mcp.tool()
async def wilcoxon(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.wilcoxon(data1, data2)
@mcp.tool()
async def kruskal(datasets: List[Union[List[float], str]]) -> Dict[str, Any]: return await stats_ops.kruskal(datasets)
@mcp.tool()
async def anova_oneway(datasets: List[Union[List[float], str]]) -> Dict[str, Any]: return await stats_ops.anova_oneway(datasets)
@mcp.tool()
async def ks_test(data: Union[List[float], str], cdf: str = 'norm') -> Dict[str, Any]: return await stats_ops.ks_test(data, cdf)

# Correlations
@mcp.tool()
async def pearson_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.pearson_corr(data1, data2)
@mcp.tool()
async def spearman_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.spearman_corr(data1, data2)
@mcp.tool()
async def kendall_corr(data1: Union[List[float], str], data2: Union[List[float], str]) -> Dict[str, Any]: return await stats_ops.kendall_corr(data1, data2)

# Fitting
@mcp.tool()
async def fit_norm(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_norm(data)
@mcp.tool()
async def fit_expon(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_expon(data)
@mcp.tool()
async def fit_gamma(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_gamma(data)
@mcp.tool()
async def fit_beta(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_beta(data)
@mcp.tool()
async def fit_lognorm(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_lognorm(data)
@mcp.tool()
async def fit_weibull(data: Union[List[float], str]) -> Dict[str, float]: return await stats_ops.fit_weibull(data)


# ==========================================
# 2. Optimization
# ==========================================
@mcp.tool()
async def minimize_scalar(func_str: str, method: str = 'brent') -> Dict[str, Any]: return await opt_ops.minimize_scalar(func_str, method)
@mcp.tool()
async def minimize_bfgs(func_str: str, x0: List[float]) -> Dict[str, Any]: return await opt_ops.minimize_bfgs(func_str, x0)
@mcp.tool()
async def minimize_nelder(func_str: str, x0: List[float]) -> Dict[str, Any]: return await opt_ops.minimize_nelder(func_str, x0)
@mcp.tool()
async def find_root(func_str: str, a: float, b: float) -> float: return await opt_ops.find_root(func_str, a, b)
@mcp.tool()
async def curve_fit(func_str: str, x_data: Union[List[float], str], y_data: Union[List[float], str]) -> Dict[str, Any]: return await opt_ops.curve_fit(func_str, x_data, y_data)
@mcp.tool()
async def linear_sum_assignment(cost_matrix: List[List[float]]) -> Dict[str, Any]: return await opt_ops.linear_sum_assignment(cost_matrix)
@mcp.tool()
async def linprog(c: List[float], A_ub: List[List[float]] = None, b_ub: List[float] = None, A_eq: List[List[float]] = None, b_eq: List[float] = None, bounds: List[List[float]] = None) -> Dict[str, Any]: return await opt_ops.linprog(c, A_ub, b_ub, A_eq, b_eq, bounds)
# Global
@mcp.tool()
async def basinhopping(func_str: str, x0: List[float], niter: int = 100) -> Dict[str, Any]: return await opt_ops.basinhopping(func_str, x0, niter)
@mcp.tool()
async def differential_evolution(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]: return await opt_ops.differential_evolution(func_str, bounds)
@mcp.tool()
async def dual_annealing(func_str: str, bounds: List[List[float]]) -> Dict[str, Any]: return await opt_ops.dual_annealing(func_str, bounds)


# ==========================================
# 3. Integration
# ==========================================
@mcp.tool()
async def integrate_quad(func_str: str, a: float, b: float) -> Dict[str, float]: return await integ_ops.integrate_quad(func_str, a, b)
@mcp.tool()
async def integrate_simpson(y_data: Union[List[float], str], x_data: Optional[Union[List[float], str]] = None, dx: float = 1.0) -> float: return await integ_ops.integrate_simpson(y_data, x_data, dx)
@mcp.tool()
async def integrate_trapezoid(y_data: Union[List[float], str], x_data: Optional[Union[List[float], str]] = None, dx: float = 1.0) -> float: return await integ_ops.integrate_trapezoid(y_data, x_data, dx)
@mcp.tool()
async def solve_ivp(func_str: str, t_span: List[float], y0: List[float], t_eval: List[float] = None) -> Dict[str, Any]: return await integ_ops.solve_ivp(func_str, t_span, y0, t_eval)


# ==========================================
# 4. Signal Processing
# ==========================================
@mcp.tool()
async def find_peaks(data: Union[List[float], str], height: Optional[float] = None, distance: Optional[int] = None) -> Dict[str, Any]: return await signal_ops.find_peaks(data, height, distance)
@mcp.tool()
async def fft(data: Union[List[float], str]) -> Dict[str, Any]: return await signal_ops.compute_fft(data)
@mcp.tool()
async def ifft(data_real: Union[List[float], str], data_imag: Optional[Union[List[float], str]] = None) -> List[float]: return await signal_ops.compute_ifft(data_real, data_imag)
@mcp.tool()
async def resample(data: Union[List[float], str], num: int) -> List[float]: return await signal_ops.resample(data, num)
@mcp.tool()
async def medfilt(data: Union[List[float], str], kernel_size: int = 3) -> List[float]: return await signal_ops.medfilt(data, kernel_size)
@mcp.tool()
async def wiener(data: Union[List[float], str]) -> List[float]: return await signal_ops.wiener(data)
@mcp.tool()
async def savgol_filter(data: Union[List[float], str], window_length: int = 5, polyorder: int = 2) -> List[float]: return await signal_ops.savgol_filter(data, window_length, polyorder)
@mcp.tool()
async def detrend(data: Union[List[float], str], type: str = 'linear') -> List[float]: return await signal_ops.detrend(data, type)


# ==========================================
# 5. Linear Algebra
# ==========================================
@mcp.tool()
async def matrix_inv(matrix: List[List[float]]) -> List[List[float]]: return await linalg_ops.matrix_inv(matrix)
@mcp.tool()
async def matrix_det(matrix: List[List[float]]) -> float: return await linalg_ops.matrix_det(matrix)
@mcp.tool()
async def matrix_norm(matrix: List[List[float]], ord: str = None) -> float: return await linalg_ops.matrix_norm(matrix, ord)
@mcp.tool()
async def solve_linear(a: List[List[float]], b: List[float]) -> List[float]: return await linalg_ops.solve_linear(a, b)
@mcp.tool()
async def svd_decomp(matrix: List[List[float]]) -> Dict[str, Any]: return await linalg_ops.svd_decomp(matrix)
@mcp.tool()
async def eig_decomp(matrix: List[List[float]]) -> Dict[str, Any]: return await linalg_ops.eig_decomp(matrix)
@mcp.tool()
async def lu_factor(matrix: List[List[float]]) -> Dict[str, Any]: return await linalg_ops.lu_factor(matrix)
@mcp.tool()
async def cholesky(matrix: List[List[float]]) -> List[List[float]]: return await linalg_ops.cholesky(matrix)


# ==========================================
# 6. Spatial
# ==========================================
@mcp.tool()
async def distance_euclidean(u: List[float], v: List[float]) -> float: return await spatial_ops.distance_euclidean(u, v)
@mcp.tool()
async def distance_cosine(u: List[float], v: List[float]) -> float: return await spatial_ops.distance_cosine(u, v)
@mcp.tool()
async def distance_matrix(x: List[List[float]], y: List[List[float]]) -> List[List[float]]: return await spatial_ops.distance_matrix(x, y)
@mcp.tool()
async def convex_hull(points: List[List[float]]) -> Dict[str, Any]: return await spatial_ops.convex_hull(points)


# ==========================================
# 7. Super Tools
# ==========================================
@mcp.tool()
async def analyze_distribution(data: List[float]) -> Dict[str, Any]: return await super_ops.analyze_distribution(data)
@mcp.tool()
async def signal_dashboard(data: List[float]) -> Dict[str, Any]: return await super_ops.signal_dashboard(data)
@mcp.tool()
async def compare_samples(sample1: List[float], sample2: List[float]) -> Dict[str, Any]: return await super_ops.compare_samples(sample1, sample2)

# ==========================================
# 8. Interpolation (Ultimate)
# ==========================================
@mcp.tool()
async def interp_1d(x: Union[List[float], str], y: Union[List[float], str], x_new: Union[List[float], str], kind: str = 'linear') -> List[float]: return await interp_ops.interp_1d(x, y, x_new, kind)
@mcp.tool()
async def interp_spline(x: Union[List[float], str], y: Union[List[float], str], x_new: Union[List[float], str], k: int = 3, s: float = 0) -> List[float]: return await interp_ops.interp_spline(x, y, x_new, k, s)
@mcp.tool()
async def grid_data(points: List[List[float]], values: Union[List[float], str], xi: List[List[float]], method: str = 'linear') -> List[float]: return await interp_ops.grid_data(points, values, xi, method)

# ==========================================
# 9. Clustering (Ultimate)
# ==========================================
@mcp.tool()
async def kmeans(data: List[List[float]], k_or_guess: Any) -> Dict[str, Any]: return await cluster_ops.kmeans(data, k_or_guess)
@mcp.tool()
async def whitening(data: List[List[float]]) -> List[List[float]]: return await cluster_ops.whitening(data)
@mcp.tool()
async def linkage_matrix(data: List[List[float]], method: str = 'single', metric: str = 'euclidean') -> List[List[float]]: return await cluster_ops.linkage_matrix(data, method, metric)
@mcp.tool()
async def fcluster(Z: List[List[float]], t: float, criterion: str = 'distance') -> List[int]: return await cluster_ops.fcluster(Z, t, criterion)

# ==========================================
# 10. ND-Image (Ultimate)
# ==========================================
@mcp.tool()
async def img_gaussian(data: List[List[float]], sigma: float) -> List[List[float]]: return await ndimage_ops.img_gaussian(data, sigma)
@mcp.tool()
async def img_sobel(data: List[List[float]], axis: int = -1) -> List[List[float]]: return await ndimage_ops.img_sobel(data, axis)
@mcp.tool()
async def img_laplace(data: List[List[float]]) -> List[List[float]]: return await ndimage_ops.img_laplace(data)
@mcp.tool()
async def img_median(data: List[List[float]], size: int = 3) -> List[List[float]]: return await ndimage_ops.img_median(data, size)
@mcp.tool()
async def center_of_mass(data: List[List[float]]) -> List[float]: return await ndimage_ops.center_of_mass(data)

# ==========================================
# 11. Special Functions (Ultimate)
# ==========================================
@mcp.tool()
async def gamma_func(z: Union[List[float], str]) -> List[float]: return await special_ops.gamma_func(z)
@mcp.tool()
async def beta_func(a: Union[List[float], str], b: Union[List[float], str]) -> List[float]: return await special_ops.beta_func(a, b)
@mcp.tool()
async def erf_func(z: Union[List[float], str]) -> List[float]: return await special_ops.erf_func(z)
@mcp.tool()
async def bessel_j0(z: Union[List[float], str]) -> List[float]: return await special_ops.bessel_j0(z)


if __name__ == "__main__":
    mcp.run()
