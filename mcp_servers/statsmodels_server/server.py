
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
#   "statsmodels",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.statsmodels_server.tools import (
    regression_ops, tsa_ops, discrete_ops, multivar_ops, 
    nonparam_ops, stat_tools_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("statsmodels_server", dependencies=["statsmodels", "scipy", "numpy", "pandas"])
DataInput = Union[List[List[float]], List[Dict[str, Any]], str]
VectorInput = Union[List[float], str]

# ==========================================
# 1. Regression
# ==========================================
# ==========================================
# 1. Regression
# ==========================================
@mcp.tool()
async def ols_model(y: DataInput, x: DataInput, formula: Optional[str] = None) -> Dict[str, Any]: 
    """CALCULATES OLS regression. [ACTION]
    
    [RAG Context]
    Ordinary Least Squares regression.
    Returns JSON dict.
    """
    return await regression_ops.ols_model(y, x, formula)

@mcp.tool()
async def wls_model(y: DataInput, x: DataInput, weights: DataInput) -> Dict[str, Any]: 
    """CALCULATES WLS regression. [ACTION]
    
    [RAG Context]
    Weighted Least Squares regression.
    Returns JSON dict.
    """
    return await regression_ops.wls_model(y, x, weights)

@mcp.tool()
async def gls_model(y: DataInput, x: DataInput, sigma: Optional[DataInput] = None) -> Dict[str, Any]: 
    """CALCULATES GLS regression. [ACTION]
    
    [RAG Context]
    Generalized Least Squares regression.
    Returns JSON dict.
    """
    return await regression_ops.gls_model(y, x, sigma)

@mcp.tool()
async def glsar_model(y: DataInput, x: DataInput, rho: int = 1) -> Dict[str, Any]: 
    """CALCULATES GLSAR. [ACTION]
    
    [RAG Context]
    GLS with Autoregressive errors.
    Returns JSON dict.
    """
    return await regression_ops.glsar_model(y, x, rho)

@mcp.tool()
async def quant_reg(y: DataInput, x: DataInput, q: float = 0.5) -> Dict[str, Any]: 
    """CALCULATES QuantReg. [ACTION]
    
    [RAG Context]
    Quantile Regression.
    Returns JSON dict.
    """
    return await regression_ops.quant_reg(y, x, q)

@mcp.tool()
async def recursive_ls(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """CALCULATES Recursive LS. [ACTION]
    
    [RAG Context]
    Recursive Least Squares (time-varying coeffs).
    Returns JSON dict.
    """
    return await regression_ops.recursive_ls(y, x)

@mcp.tool()
async def bulk_ols(y: DataInput, x: DataInput) -> List[Dict[str, Any]]: 
    """CALCULATES Bulk OLS. [ACTION]
    
    [RAG Context]
    Run multiple OLS models in parallel.
    Returns list of model dicts.
    """
    return await regression_ops.bulk_ols(y, x)

# ==========================================
# 2. TSA
# ==========================================
@mcp.tool()
async def adfuller_test(x: VectorInput, autolag: str = 'AIC') -> Dict[str, Any]: 
    """PERFORMS ADF test. [ACTION]
    
    [RAG Context]
    Augmented Dickey-Fuller unit root test.
    Returns JSON dict.
    """
    return await tsa_ops.adfuller_test(x, autolag)

@mcp.tool()
async def kpss_test(x: VectorInput, regression: str = 'c') -> Dict[str, Any]: 
    """PERFORMS KPSS test. [ACTION]
    
    [RAG Context]
    Kwiatkowski-Phillips-Schmidt-Shin test for stationarity.
    Returns JSON dict.
    """
    return await tsa_ops.kpss_test(x, regression)

@mcp.tool()
async def decompose(x: VectorInput, model: str = 'additive', period: Optional[int] = None) -> Dict[str, Any]: 
    """DECOMPOSES series. [ACTION]
    
    [RAG Context]
    Seasonal decomposition (trend, seasonal, resid).
    Returns JSON dict.
    """
    return await tsa_ops.decompose(x, model, period)

@mcp.tool()
async def compute_acf(x: VectorInput, nlags: int = 40) -> List[float]: 
    """CALCULATES ACF. [ACTION]
    
    [RAG Context]
    Autocorrelation Function.
    Returns list of floats.
    """
    return await tsa_ops.compute_acf(x, nlags)

@mcp.tool()
async def compute_pacf(x: VectorInput, nlags: int = 40) -> List[float]: 
    """CALCULATES PACF. [ACTION]
    
    [RAG Context]
    Partial Autocorrelation Function.
    Returns list of floats.
    """
    return await tsa_ops.compute_pacf(x, nlags)

@mcp.tool()
async def arima_model(endog: VectorInput, order: List[int] = [1, 0, 0]) -> Dict[str, Any]: 
    """CALCULATES ARIMA. [ACTION]
    
    [RAG Context]
    AutoRegressive Integrated Moving Average model.
    Returns JSON dict.
    """
    return await tsa_ops.arima_model(endog, order)

@mcp.tool()
async def sarimax_model(endog: VectorInput, order: List[int], seasonal_order: List[int], exog: Optional[DataInput] = None) -> Dict[str, Any]: 
    """CALCULATES SARIMAX. [ACTION]
    
    [RAG Context]
    Seasonal ARIMA with eXogenous regressors.
    Returns JSON dict.
    """
    return await tsa_ops.sarimax_model(endog, order, seasonal_order, exog)

@mcp.tool()
async def exp_smoothing(endog: VectorInput, trend: str = None, seasonal: str = None, seasonal_periods: int = None) -> Dict[str, Any]: 
    """CALCULATES ExpSmoothing. [ACTION]
    
    [RAG Context]
    Exponential Smoothing (Holt-Winters).
    Returns JSON dict.
    """
    return await tsa_ops.exp_smoothing(endog, trend, seasonal, seasonal_periods)

@mcp.tool()
async def granger_test(data: DataInput, maxlag: int = 4) -> Dict[str, Any]: 
    """PERFORMS Granger test. [ACTION]
    
    [RAG Context]
    Granger Causality test.
    Returns JSON dict.
    """
    return await tsa_ops.granger_test(data, maxlag)

@mcp.tool()
async def auto_select_order(y: VectorInput, max_ar: int = 4, max_ma: int = 2) -> Dict[str, Any]: 
    """SELECTS ARIMA order. [ACTION]
    
    [RAG Context]
    Automatically select best (p, d, q) order.
    Returns JSON dict.
    """
    return await tsa_ops.auto_select_order(y, max_ar, max_ma)

# ==========================================
# 3. Discrete
# ==========================================
# ==========================================
# 3. Discrete
# ==========================================
@mcp.tool()
async def logit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """CALCULATES Logit. [ACTION]
    
    [RAG Context]
    Logistic Regression (Binary classification).
    Returns JSON dict.
    """
    return await discrete_ops.logit_model(y, x)

@mcp.tool()
async def probit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """CALCULATES Probit. [ACTION]
    
    [RAG Context]
    Probit Regression (Binary classification).
    Returns JSON dict.
    """
    return await discrete_ops.probit_model(y, x)

@mcp.tool()
async def mnlogit_model(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """CALCULATES MNLogit. [ACTION]
    
    [RAG Context]
    Multinomial Logistic Regression.
    Returns JSON dict.
    """
    return await discrete_ops.mnlogit_model(y, x)

@mcp.tool()
async def poisson_model(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """CALCULATES Poisson. [ACTION]
    
    [RAG Context]
    Poisson Regression (Count data).
    Returns JSON dict.
    """
    return await discrete_ops.poisson_model(y, x)

@mcp.tool()
async def neg_binom_model(y: DataInput, x: DataInput, alpha: float = 1.0) -> Dict[str, Any]: 
    """CALCULATES NegBinom. [ACTION]
    
    [RAG Context]
    Negative Binomial Regression (Count data).
    Returns JSON dict.
    """
    return await discrete_ops.neg_binom_model(y, x, alpha)

# ==========================================
# 4. Multivar
# ==========================================
@mcp.tool()
async def pca(data: DataInput, ncomp: Optional[int] = None, standardize: bool = True) -> Dict[str, Any]: 
    """PERFORMS PCA. [ACTION]
    
    [RAG Context]
    Principal Component Analysis.
    Returns JSON dict.
    """
    return await multivar_ops.pca(data, ncomp, standardize)

@mcp.tool()
async def factor_analysis(data: DataInput, n_factor: int = 1) -> Dict[str, Any]: 
    """PERFORMS FactorAnalysis. [ACTION]
    
    [RAG Context]
    Factor Analysis.
    Returns JSON dict.
    """
    return await multivar_ops.factor_analysis(data, n_factor)

@mcp.tool()
async def manova(endog: DataInput, exog: DataInput) -> Dict[str, Any]: 
    """PERFORMS MANOVA. [ACTION]
    
    [RAG Context]
    Multivariate Analysis of Variance.
    Returns JSON dict.
    """
    return await multivar_ops.manova(endog, exog)

@mcp.tool()
async def canon_corr(endog: DataInput, exog: DataInput) -> Dict[str, Any]: 
    """CALCULATES CanonicalCorr. [ACTION]
    
    [RAG Context]
    Canonical Correlation Analysis.
    Returns JSON dict.
    """
    return await multivar_ops.canon_corr(endog, exog)

# ==========================================
# 5. Nonparam
# ==========================================
# ==========================================
# 5. Nonparam
# ==========================================
@mcp.tool()
async def kde_univar(data: VectorInput, kernel: str = 'gau', fft: bool = True) -> Dict[str, Any]: 
    """CALCULATES KDE univar. [ACTION]
    
    [RAG Context]
    Univariate Kernel Density Estimation.
    Returns JSON dict.
    """
    return await nonparam_ops.kde_univar(data, kernel, fft)

@mcp.tool()
async def kde_multivar(data: DataInput, var_type: str) -> Dict[str, Any]: 
    """CALCULATES KDE multivar. [ACTION]
    
    [RAG Context]
    Multivariate Kernel Density Estimation.
    Returns JSON dict.
    """
    return await nonparam_ops.kde_multivar(data, var_type)

@mcp.tool()
async def lowess(endog: VectorInput, exog: VectorInput, frac: float = 2.0/3.0, it: int = 3) -> List[List[float]]: 
    """CALCULATES LOWESS. [ACTION]
    
    [RAG Context]
    Locally Weighted Scatterplot Smoothing.
    Returns list of lists.
    """
    return await nonparam_ops.lowess(endog, exog, frac, it)

# ==========================================
# 6. Stat Tools
# ==========================================
@mcp.tool()
async def jarque_bera_test(resids: VectorInput) -> Dict[str, Any]: 
    """PERFORMS Jarque-Bera. [ACTION]
    
    [RAG Context]
    Test for normality of residuals.
    Returns JSON dict.
    """
    return await stat_tools_ops.jarque_bera_test(resids)

@mcp.tool()
async def omni_normtest_test(resids: VectorInput) -> Dict[str, Any]: 
    """PERFORMS OmniNorm test. [ACTION]
    
    [RAG Context]
    Omnibus test for normality.
    Returns JSON dict.
    """
    return await stat_tools_ops.omni_normtest_test(resids)

@mcp.tool()
async def durbin_watson_test(resids: VectorInput) -> float: 
    """PERFORMS Durbin-Watson. [ACTION]
    
    [RAG Context]
    Test for autocorrelation in residuals.
    Returns float.
    """
    return await stat_tools_ops.durbin_watson_test(resids)

@mcp.tool()
async def het_breuschpagan_test(resids: VectorInput, exog: DataInput) -> Dict[str, Any]: 
    """PERFORMS Breusch-Pagan. [ACTION]
    
    [RAG Context]
    Test for heteroscedasticity.
    Returns JSON dict.
    """
    return await stat_tools_ops.het_breuschpagan_test(resids, exog)

@mcp.tool()
async def het_goldfeldquandt_test(y: VectorInput, x: DataInput) -> Dict[str, Any]: 
    """PERFORMS Goldfeld-Quandt. [ACTION]
    
    [RAG Context]
    Test for heteroscedasticity.
    Returns JSON dict.
    """
    return await stat_tools_ops.het_goldfeldquandt_test(y, x)

@mcp.tool()
async def stats_describe(data: DataInput) -> Dict[str, Any]: 
    """DESCRIBES statistics. [ACTION]
    
    [RAG Context]
    Get descriptive statistics (mean, std, min, max, etc).
    Returns JSON dict.
    """
    return await stat_tools_ops.stats_describe(data)

@mcp.tool()
async def z_test(x1: VectorInput, x2: Optional[VectorInput] = None, value: float = 0) -> Dict[str, Any]: 
    """PERFORMS Z-test. [ACTION]
    
    [RAG Context]
    Test for mean difference.
    Returns JSON dict.
    """
    return await stat_tools_ops.z_test(x1, x2, value)

@mcp.tool()
async def prop_confint(count: int, nobs: int, alpha: float = 0.05) -> List[float]: 
    """CALCULATES Prop ConfInt. [ACTION]
    
    [RAG Context]
    Confidence interval for proportion.
    Returns list of floats.
    """
    return await stat_tools_ops.prop_confint(count, nobs, alpha)

# ==========================================
# 7. Super
# ==========================================
@mcp.tool()
async def automl_regression(y: DataInput, x: DataInput) -> Dict[str, Any]: 
    """PERFORMS AutoML Regression. [ACTION]
    
    [RAG Context]
    Automatically try multiple regression models and select best.
    Returns JSON dict.
    """
    return await super_ops.automl_regression(y, x)

@mcp.tool()
async def tsa_dashboard(y: DataInput, period: int = 12) -> Dict[str, Any]: 
    """GENERATES TSA Dashboard. [ACTION]
    
    [RAG Context]
    Comprehensive Time Series Analysis report.
    Returns JSON dict.
    """
    return await super_ops.tsa_dashboard(y, period)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class StatsmodelsServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
