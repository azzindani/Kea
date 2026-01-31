# /// script
# dependencies = [
#   "mcp",
#   "numpy",
#   "pandas",
#   "scipy",
#   "statsmodels",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    regression_ops, tsa_ops, discrete_ops, multivar_ops, 
    nonparam_ops, stat_tools_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("statsmodels_server", dependencies=["statsmodels", "scipy", "numpy", "pandas"])
DataInput = Union[List[List[float]], List[Dict[str, Any]], str]
VectorInput = Union[List[float], str]

# ==========================================
# 1. Regression
# ==========================================
@mcp.tool()
async def ols_model(y: DataInput, x: DataInput, formula: Optional[str] = None) -> Dict[str, Any]: return await regression_ops.ols_model(y, x, formula)
@mcp.tool()
async def wls_model(y: DataInput, x: DataInput, weights: DataInput) -> Dict[str, Any]: return await regression_ops.wls_model(y, x, weights)
@mcp.tool()
async def gls_model(y: DataInput, x: DataInput, sigma: Optional[DataInput] = None) -> Dict[str, Any]: return await regression_ops.gls_model(y, x, sigma)
@mcp.tool()
async def glsar_model(y: DataInput, x: DataInput, rho: int = 1) -> Dict[str, Any]: return await regression_ops.glsar_model(y, x, rho)
@mcp.tool()
async def quant_reg(y: DataInput, x: DataInput, q: float = 0.5) -> Dict[str, Any]: return await regression_ops.quant_reg(y, x, q)
@mcp.tool()
async def recursive_ls(y: DataInput, x: DataInput) -> Dict[str, Any]: return await regression_ops.recursive_ls(y, x)
@mcp.tool()
async def bulk_ols(y: DataInput, x: DataInput) -> List[Dict[str, Any]]: return await regression_ops.bulk_ols(y, x)

# ==========================================
# 2. TSA
# ==========================================
@mcp.tool()
async def adfuller_test(x: VectorInput, autolag: str = 'AIC') -> Dict[str, Any]: return await tsa_ops.adfuller_test(x, autolag)
@mcp.tool()
async def kpss_test(x: VectorInput, regression: str = 'c') -> Dict[str, Any]: return await tsa_ops.kpss_test(x, regression)
@mcp.tool()
async def decompose(x: VectorInput, model: str = 'additive', period: Optional[int] = None) -> Dict[str, Any]: return await tsa_ops.decompose(x, model, period)
@mcp.tool()
async def compute_acf(x: VectorInput, nlags: int = 40) -> List[float]: return await tsa_ops.compute_acf(x, nlags)
@mcp.tool()
async def compute_pacf(x: VectorInput, nlags: int = 40) -> List[float]: return await tsa_ops.compute_pacf(x, nlags)
@mcp.tool()
async def arima_model(endog: VectorInput, order: List[int] = [1, 0, 0]) -> Dict[str, Any]: return await tsa_ops.arima_model(endog, order)
@mcp.tool()
async def sarimax_model(endog: VectorInput, order: List[int], seasonal_order: List[int], exog: Optional[DataInput] = None) -> Dict[str, Any]: return await tsa_ops.sarimax_model(endog, order, seasonal_order, exog)
@mcp.tool()
async def exp_smoothing(endog: VectorInput, trend: str = None, seasonal: str = None, seasonal_periods: int = None) -> Dict[str, Any]: return await tsa_ops.exp_smoothing(endog, trend, seasonal, seasonal_periods)
@mcp.tool()
async def granger_test(data: DataInput, maxlag: int = 4) -> Dict[str, Any]: return await tsa_ops.granger_test(data, maxlag)
@mcp.tool()
async def auto_select_order(y: VectorInput, max_ar: int = 4, max_ma: int = 2) -> Dict[str, Any]: return await tsa_ops.auto_select_order(y, max_ar, max_ma)

# ==========================================
# 3. Discrete
# ==========================================
@mcp.tool()
async def logit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: return await discrete_ops.logit_model(y, x)
@mcp.tool()
async def probit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: return await discrete_ops.probit_model(y, x)
@mcp.tool()
async def mnlogit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: return await discrete_ops.mnlogit_model(y, x)
@mcp.tool()
async def poisson_model(y: DataInput, x: DataInput) -> Dict[str, Any]: return await discrete_ops.poisson_model(y, x)
@mcp.tool()
async def neg_binom_model(y: DataInput, x: DataInput, alpha: float = 1.0) -> Dict[str, Any]: return await discrete_ops.neg_binom_model(y, x, alpha)

# ==========================================
# 4. Multivar
# ==========================================
@mcp.tool()
async def pca(data: DataInput, ncomp: Optional[int] = None, standardize: bool = True) -> Dict[str, Any]: return await multivar_ops.pca(data, ncomp, standardize)
@mcp.tool()
async def factor_analysis(data: DataInput, n_factor: int = 1) -> Dict[str, Any]: return await multivar_ops.factor_analysis(data, n_factor)
@mcp.tool()
async def manova(endog: DataInput, exog: DataInput) -> Dict[str, Any]: return await multivar_ops.manova(endog, exog)
@mcp.tool()
async def canon_corr(endog: DataInput, exog: DataInput) -> Dict[str, Any]: return await multivar_ops.canon_corr(endog, exog)

# ==========================================
# 5. Nonparam
# ==========================================
@mcp.tool()
async def kde_univar(data: VectorInput, kernel: str = 'gau', fft: bool = True) -> Dict[str, Any]: return await nonparam_ops.kde_univar(data, kernel, fft)
@mcp.tool()
async def kde_multivar(data: DataInput, var_type: str) -> Dict[str, Any]: return await nonparam_ops.kde_multivar(data, var_type)
@mcp.tool()
async def lowess(endog: VectorInput, exog: VectorInput, frac: float = 2.0/3.0, it: int = 3) -> List[List[float]]: return await nonparam_ops.lowess(endog, exog, frac, it)

# ==========================================
# 6. Stat Tools
# ==========================================
@mcp.tool()
async def jarque_bera_test(resids: VectorInput) -> Dict[str, Any]: return await stat_tools_ops.jarque_bera_test(resids)
@mcp.tool()
async def omni_normtest_test(resids: VectorInput) -> Dict[str, Any]: return await stat_tools_ops.omni_normtest_test(resids)
@mcp.tool()
async def durbin_watson_test(resids: VectorInput) -> float: return await stat_tools_ops.durbin_watson_test(resids)
@mcp.tool()
async def het_breuschpagan_test(resids: VectorInput, exog: DataInput) -> Dict[str, Any]: return await stat_tools_ops.het_breuschpagan_test(resids, exog)
@mcp.tool()
async def het_goldfeldquandt_test(y: VectorInput, x: DataInput) -> Dict[str, Any]: return await stat_tools_ops.het_goldfeldquandt_test(y, x)
@mcp.tool()
async def stats_describe(data: DataInput) -> Dict[str, Any]: return await stat_tools_ops.stats_describe(data)
@mcp.tool()
async def z_test(x1: VectorInput, x2: Optional[VectorInput] = None, value: float = 0) -> Dict[str, Any]: return await stat_tools_ops.z_test(x1, x2, value)
@mcp.tool()
async def prop_confint(count: int, nobs: int, alpha: float = 0.05) -> List[float]: return await stat_tools_ops.prop_confint(count, nobs, alpha)

# ==========================================
# 7. Super
# ==========================================
@mcp.tool()
async def automl_regression(y: DataInput, x: DataInput) -> Dict[str, Any]: return await super_ops.automl_regression(y, x)
@mcp.tool()
async def tsa_dashboard(y: DataInput, period: int = 12) -> Dict[str, Any]: return await super_ops.tsa_dashboard(y, period)


if __name__ == "__main__":
    mcp.run()
