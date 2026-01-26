from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, to_serializable, format_summary, DataInput
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def _fit_and_summarize(model) -> Dict[str, Any]:
    results = model.fit()
    return to_serializable({
        "params": results.params,
        "pvalues": results.pvalues,
        "rsquared": getattr(results, "rsquared", None),
        "aic": getattr(results, "aic", None),
        "bic": getattr(results, "bic", None),
        "conf_int": results.conf_int(),
        "summary": format_summary(results)
    })

async def ols_model(y: DataInput, x: DataInput, formula: Optional[str] = None) -> Dict[str, Any]:
    """
    Ordinary Least Squares.
    If formula provided (e.g. "y ~ x + a"), uses R-style formulas.
    Else x/y arrays.
    """
    if formula:
        if isinstance(y, str) and not isinstance(x, str):
             # data usually passed as single dataframe for formulas
             # let's assume y is the dataframe if x is None or y contains all cols
             df = parse_dataframe(y)
             return await _fit_and_summarize(smf.ols(formula=formula, data=df))
        else:
             # Try merging?
             # For simplicity, if formula used, data must be in y argument as DataFrame
             df = parse_dataframe(y)
             return await _fit_and_summarize(smf.ols(formula=formula, data=df))
             
    # Array based
    y_arr = parse_dataframe(y)
    x_arr = parse_dataframe(x)
    x_arr = sm.add_constant(x_arr) # Auto add constant
    return await _fit_and_summarize(sm.OLS(y_arr, x_arr))

async def wls_model(y: DataInput, x: DataInput, weights: DataInput) -> Dict[str, Any]:
    """Weighted Least Squares."""
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    w_arr = parse_dataframe(weights)
    return await _fit_and_summarize(sm.WLS(y_arr, x_arr, weights=w_arr))

async def gls_model(y: DataInput, x: DataInput, sigma: Optional[DataInput] = None) -> Dict[str, Any]:
    """Generalized Least Squares."""
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    return await _fit_and_summarize(sm.GLS(y_arr, x_arr, sigma=sigma))

async def glsar_model(y: DataInput, x: DataInput, rho: int = 1) -> Dict[str, Any]:
    """GLS with AR(p) errors."""
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    model = sm.GLSAR(y_arr, x_arr, rho=rho)
    res = model.iterative_fit(1)
    return to_serializable({
        "params": res.params,
        "summary": format_summary(res)
    })

async def quant_reg(y: DataInput, x: DataInput, q: float = 0.5) -> Dict[str, Any]:
    """Quantile Regression."""
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    res = sm.QuantReg(y_arr, x_arr).fit(q=q)
    return to_serializable({
        "params": res.params,
        "summary": format_summary(res)
    })

async def recursive_ls(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """Recursive Least Squares."""
    y_arr = parse_dataframe(y)
    x_arr = sm.add_constant(parse_dataframe(x))
    res = sm.RecursiveLS(y_arr, x_arr).fit()
    return to_serializable({
        "params": res.params,
        "cusum": res.cusum,
        "summary": format_summary(res)
    })

async def bulk_ols(y: DataInput, x: DataInput) -> List[Dict[str, Any]]:
    """
    Run OLS for multiple Y columns against same X.
    Y should be a dataframe with multiple columns.
    """
    y_df = parse_dataframe(y)
    x_df = sm.add_constant(parse_dataframe(x))
    
    results = []
    for col in y_df.columns:
        res = sm.OLS(y_df[col], x_df).fit()
        results.append({
            "target": str(col),
            "rsquared": res.rsquared,
            "params": to_serializable(res.params)
        })
    return results
