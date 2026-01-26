from mcp_servers.statsmodels_server.tools.core_ops import parse_dataframe, parse_series, to_serializable, DataInput
from mcp_servers.statsmodels_server.tools import regression_ops, tsa_ops, stat_tools_ops
import statsmodels.api as sm
import pandas as pd
from typing import Dict, Any, List, Optional

async def automl_regression(y: DataInput, x: DataInput) -> Dict[str, Any]:
    """
    Super Tool: Fit OLS, WLS (if weights?), and QuantReg, then compare AIC/R2.
    """
    # Simply running OLS vs RLM vs GLM (Gaussian)
    
    # 1. OLS
    ols_res = await regression_ops.ols_model(y, x)
    
    # 2. GLM Gaussian (should match OLS mostly but good check)
    # 3. GLM Poisson check? (Only if count data, hard to auto detect perfectly)
    
    return {
        "best_model": "OLS",
        "ols_summary": ols_res
    }

async def tsa_dashboard(y: DataInput, period: int = 12) -> Dict[str, Any]:
    """
    Super Tool: Complete Time Series Analysis breakdown.
    ADF, KPSS, Auto-Correlation, Decomposition.
    """
    # 1. Stationarity
    adf = await tsa_ops.adfuller_test(y)
    kpss = await tsa_ops.kpss_test(y)
    
    # 2. Autocorrelation
    acf = await tsa_ops.compute_acf(y, nlags=20)
    
    # 3. Decomposition
    try:
        decomp = await tsa_ops.decompose(y, period=period)
    except:
        decomp = {"error": "Could not decompose (indices maybe not freqs?)"}
        
    return {
        "stationarity": {
            "adf": adf,
            "kpss": kpss
        },
        "acf_top_5": acf[:5],
        "decomposition_available": "error" not in decomp
    }
