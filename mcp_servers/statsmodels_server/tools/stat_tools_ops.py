from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, parse_series, to_serializable, DataInput, VectorInput
import statsmodels.stats.api as sms
import statsmodels.stats.descriptivestats as desc
from statsmodels.stats.weightstats import ztest
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.stattools import jarque_bera, durbin_watson, omni_normtest
from statsmodels.stats.diagnostic import het_breuschpagan, het_goldfeldquandt, linear_rainbow
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

async def jarque_bera_test(resids: VectorInput) -> Dict[str, Any]:
    """Jarque-Bera normality test."""
    score, p, skew, kurt = jarque_bera(parse_series(resids))
    return to_serializable({"stats": score, "pvalue": p, "skew": skew, "kurtosis": kurt})

async def omni_normtest_test(resids: VectorInput) -> Dict[str, Any]:
    """Omnibus test for normality."""
    score, p = omni_normtest(parse_series(resids))
    return to_serializable({"chisq": score, "pvalue": p})

async def durbin_watson_test(resids: VectorInput) -> float:
    """Durbin-Watson test for autocorrelation (target 2.0)."""
    return float(durbin_watson(parse_series(resids)))

async def het_breuschpagan_test(resids: VectorInput, exog: DataInput) -> Dict[str, Any]:
    """Breusch-Pagan Lagrange Multiplier test for heteroscedasticity."""
    ex = parse_dataframe(exog)
    lm, p_lm, f_val, p_f = het_breuschpagan(parse_series(resids), ex)
    return to_serializable({"lm": lm, "p_lm": p_lm, "f_stat": f_val, "p_f": p_f})

async def het_goldfeldquandt_test(y: VectorInput, x: DataInput) -> Dict[str, Any]:
    """Goldfeld-Quandt homoskedasticity test."""
    f, p, order = het_goldfeldquandt(parse_series(y), parse_dataframe(x))
    return to_serializable({"f_stat": f, "pvalue": p, "ordering": order})

async def linear_rainbow_test(res: Any) -> Dict[str, Any]:
    """Rainbow test for linearity."""
    # Needs result object? No, function takes (res, ...). 
    # But passing result object via JSON API is impossible.
    # statsmodels diagnostic functions usually take "resid". Rainbow takes "res" (result wrapper)?
    # Actually linear_rainbow takes (res). We can't use it easily in disconnected mode without pickling.
    # Skipping for now or implementing if we had the result in memory (not stateless tool calls).
    return {"error": "Requires active model result object in memory."}

async def stats_describe(data: DataInput) -> Dict[str, Any]:
    """Extended descriptive statistics."""
    df = parse_dataframe(data)
    d = desc.describe(df)
    return to_serializable(d) # Returns dataframe

async def z_test(x1: VectorInput, x2: Optional[VectorInput] = None, value: float = 0) -> Dict[str, Any]:
    """Z-test for mean."""
    stat, p = ztest(parse_series(x1), parse_series(x2) if x2 else None, value=value)
    return to_serializable({"statistic": stat, "pvalue": p})

async def prop_confint(count: int, nobs: int, alpha: float = 0.05) -> List[float]:
    """Confidence interval for a binomial proportion."""
    low, high = proportion_confint(count, nobs, alpha=alpha)
    return to_serializable([low, high])
