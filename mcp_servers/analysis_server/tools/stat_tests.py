import pandas as pd
from scipy import stats
import structlog
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

def _run_test(test_func, **kwargs) -> Dict[str, Any]:
    try:
        stat, p_value = test_func(**kwargs)
        return {
            "statistic": float(stat),
            "p_value": float(p_value),
            "significant_05": float(p_value) < 0.05,
            "significant_01": float(p_value) < 0.01
        }
    except Exception as e:
        return {"error": str(e)}

def _get_series(file_path: str, column: str) -> pd.Series:
    df = pd.read_csv(file_path)
    return df[column].dropna()

# --- Parametric Tests ---
def test_ttest_1samp(file_path: str, column: str, population_mean: float) -> Dict[str, Any]:
    """PERFORMS One-Sample T-Test. [DATA]"""
    data = _get_series(file_path, column)
    return _run_test(stats.ttest_1samp, a=data, popmean=population_mean)

def test_ttest_ind(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Independent T-Test. [DATA]"""
    data1 = _get_series(file_path1, col1)
    data2 = _get_series(file_path2, col2)
    return _run_test(stats.ttest_ind, a=data1, b=data2)

def test_ttest_rel(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Paired T-Test. [DATA]"""
    df = pd.read_csv(file_path)
    # Must drop rows where either is NaN to maintain pairing
    df_clean = df[[col1, col2]].dropna()
    return _run_test(stats.ttest_rel, a=df_clean[col1], b=df_clean[col2])

# --- Non-Parametric Tests ---
def test_mannwhitneyu(file_path1: str, col1: str, file_path2: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Mann-Whitney U Test. [DATA]"""
    data1 = _get_series(file_path1, col1)
    data2 = _get_series(file_path2, col2)
    return _run_test(stats.mannwhitneyu, x=data1, y=data2)

def test_wilcoxon(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Wilcoxon Signed-Rank Test. [DATA]"""
    df = pd.read_csv(file_path)
    df_clean = df[[col1, col2]].dropna()
    return _run_test(stats.wilcoxon, x=df_clean[col1], y=df_clean[col2])

def test_kruskal(file_path: str, group_col: str, value_col: str) -> Dict[str, Any]:
    """PERFORMS Kruskal-Wallis H Test. [DATA]"""
    df = pd.read_csv(file_path)
    groups = [group[value_col].dropna().values for name, group in df.groupby(group_col)]
    return _run_test(stats.kruskal, *groups)

# --- Correlation ---
def test_pearsonr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Pearson Correlation. [DATA]"""
    df = pd.read_csv(file_path)
    df_clean = df[[col1, col2]].dropna()
    return _run_test(stats.pearsonr, x=df_clean[col1], y=df_clean[col2])

def test_spearmanr(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Spearman Correlation. [DATA]"""
    df = pd.read_csv(file_path)
    df_clean = df[[col1, col2]].dropna()
    return _run_test(stats.spearmanr, a=df_clean[col1], b=df_clean[col2])

def test_kendalltau(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """CALCULATES Kendall's Tau. [DATA]"""
    df = pd.read_csv(file_path)
    df_clean = df[[col1, col2]].dropna()
    return _run_test(stats.kendalltau, x=df_clean[col1], y=df_clean[col2])

# --- Distribution ---
def test_shapiro(file_path: str, column: str) -> Dict[str, Any]:
    """PERFORMS Shapiro-Wilk Normality Test. [DATA]"""
    data = _get_series(file_path, column)
    return _run_test(stats.shapiro, x=data)

def test_normaltest(file_path: str, column: str) -> Dict[str, Any]:
    """PERFORMS D'Agostino's K^2 Test. [DATA]"""
    data = _get_series(file_path, column)
    return _run_test(stats.normaltest, a=data)

def test_kstest(file_path: str, column: str, cdf: str = 'norm') -> Dict[str, Any]:
    """PERFORMS Kolmogorov-Smirnov Test. [DATA]"""
    data = _get_series(file_path, column)
    return _run_test(stats.kstest, rvs=data, cdf=cdf)

# --- Categorical ---
def test_chi2_contingency(file_path: str, col1: str, col2: str) -> Dict[str, Any]:
    """PERFORMS Chi-Square Test of Independence. [DATA]"""
    try:
        df = pd.read_csv(file_path)
        contingency = pd.crosstab(df[col1], df[col2])
        chi2, p, dof, expected = stats.chi2_contingency(contingency)
        return {
            "chi2": chi2, "p_value": p, "dof": dof, 
            "significant_05": p < 0.05
        }
    except Exception as e:
        return {"error": str(e)}
