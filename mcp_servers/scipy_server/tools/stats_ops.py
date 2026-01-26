from mcp_servers.scipy_server.tools.core_ops import parse_data, to_serializable, NumericData
from scipy import stats
import numpy as np
from typing import Dict, Any, List, Optional, Union

# ==========================================
# Descriptive Statistics
# ==========================================
async def describe_data(data: NumericData) -> Dict[str, Any]:
    """
    Get detailed descriptive statistics: nobs, minmax, mean, variance, skewness, kurtosis.
    """
    arr = parse_data(data)
    desc = stats.describe(arr)
    return to_serializable({
        "nobs": desc.nobs,
        "min": desc.minmax[0],
        "max": desc.minmax[1],
        "mean": desc.mean,
        "variance": desc.variance,
        "skewness": desc.skewness,
        "kurtosis": desc.kurtosis
    })

async def get_percentiles(data: NumericData, percentiles: List[float] = [25, 50, 75]) -> Dict[str, float]:
    """Calculate specific percentiles."""
    arr = parse_data(data)
    res = np.percentile(arr, percentiles)
    return {f"{p}%": float(v) for p, v in zip(percentiles, res)}

async def get_zscore(data: NumericData) -> List[float]:
    """Calculate Z-scores."""
    arr = parse_data(data)
    return to_serializable(stats.zscore(arr))

async def get_iqr(data: NumericData) -> float:
    """Calculate Interquartile Range."""
    arr = parse_data(data)
    return float(stats.iqr(arr))

async def get_entropy(data: NumericData) -> float:
    """Calculate entropy of distribution."""
    arr = parse_data(data)
    return float(stats.entropy(arr))

async def get_mode(data: NumericData) -> Dict[str, Any]:
    """Calculate mode."""
    arr = parse_data(data)
    res = stats.mode(arr, keepdims=True)
    return to_serializable({"mode": res.mode[0], "count": res.count[0]})

# ==========================================
# Statistical Tests
# ==========================================
async def test_normality(data: NumericData) -> Dict[str, Any]:
    """
    Test if data comes from normal distribution using Shapiro-Wilk and Normaltest (D'Agostino's K^2).
    """
    arr = parse_data(data)
    shapiro = stats.shapiro(arr)
    k2 = stats.normaltest(arr)
    return to_serializable({
        "shapiro": {"statistic": shapiro.statistic, "pvalue": shapiro.pvalue},
        "normaltest": {"statistic": k2.statistic, "pvalue": k2.pvalue},
        "is_normal_005": shapiro.pvalue > 0.05
    })

async def ttest_ind(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """T-test for two independent samples."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.ttest_ind(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def ttest_rel(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """T-test for two related samples."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.ttest_rel(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def mannwhitneyu(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """Mann-Whitney U rank test."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.mannwhitneyu(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def wilcoxon(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """Wilcoxon signed-rank test."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.wilcoxon(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def kruskal(datasets: List[NumericData]) -> Dict[str, Any]:
    """Kruskal-Wallis H-test for independent samples."""
    arrays = [parse_data(d) for d in datasets]
    res = stats.kruskal(*arrays)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def anova_oneway(datasets: List[NumericData]) -> Dict[str, Any]:
    """One-way ANOVA."""
    arrays = [parse_data(d) for d in datasets]
    res = stats.f_oneway(*arrays)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def ks_test(data: NumericData, cdf: str = 'norm') -> Dict[str, Any]:
    """Kolmogorov-Smirnov test for goodness of fit."""
    arr = parse_data(data)
    res = stats.kstest(arr, cdf)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

# ==========================================
# Correlations
# ==========================================
async def pearson_corr(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """Pearson correlation coefficient."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.pearsonr(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def spearman_corr(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """Spearman rank-order correlation."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.spearmanr(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

async def kendall_corr(data1: NumericData, data2: NumericData) -> Dict[str, Any]:
    """Kendall's tau correlation."""
    a = parse_data(data1)
    b = parse_data(data2)
    res = stats.kendalltau(a, b)
    return to_serializable({"statistic": res.statistic, "pvalue": res.pvalue})

# ==========================================
# Distribution Fitting
# ==========================================
async def fit_norm(data: NumericData) -> Dict[str, float]:
    """Fit Normal distribution."""
    arr = parse_data(data)
    loc, scale = stats.norm.fit(arr)
    return {"loc": float(loc), "scale": float(scale)}

async def fit_expon(data: NumericData) -> Dict[str, float]:
    """Fit Exponential distribution."""
    arr = parse_data(data)
    loc, scale = stats.expon.fit(arr)
    return {"loc": float(loc), "scale": float(scale)}

async def fit_gamma(data: NumericData) -> Dict[str, float]:
    """Fit Gamma distribution."""
    arr = parse_data(data)
    a, loc, scale = stats.gamma.fit(arr)
    return {"a": float(a), "loc": float(loc), "scale": float(scale)}

async def fit_beta(data: NumericData) -> Dict[str, float]:
    """Fit Beta distribution."""
    arr = parse_data(data)
    a, b, loc, scale = stats.beta.fit(arr)
    return {"a": float(a), "b": float(b), "loc": float(loc), "scale": float(scale)}

async def fit_lognorm(data: NumericData) -> Dict[str, float]:
    """Fit Log-Normal distribution."""
    arr = parse_data(data)
    s, loc, scale = stats.lognorm.fit(arr)
    return {"s": float(s), "loc": float(loc), "scale": float(scale)}

async def fit_weibull(data: NumericData) -> Dict[str, float]:
    """Fit Weibull (min) distribution."""
    arr = parse_data(data)
    c, loc, scale = stats.weibull_min.fit(arr)
    return {"c": float(c), "loc": float(loc), "scale": float(scale)}
