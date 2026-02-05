from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import risk_models
import pandas as pd
from typing import Dict, Any, List

def _cov_to_json(cov_df: pd.DataFrame) -> str:
    return cov_df.to_json(orient='split')

def sample_cov(prices_input: str, frequency: int = 252, log_returns: bool = False) -> str:
    """Calculate the annualized sample covariance matrix."""
    df = _parse_prices(prices_input)
    S = risk_models.sample_cov(df, frequency=frequency, log_returns=log_returns)
    return _cov_to_json(S)

def semicovariance(prices_input: str, benchmark: float = 0, frequency: int = 252, log_returns: bool = False) -> str:
    """Calculate the annualized semicovariance matrix (downside deviation)."""
    df = _parse_prices(prices_input)
    S = risk_models.semicovariance(df, benchmark=benchmark, frequency=frequency, log_returns=log_returns)
    return _cov_to_json(S)

def exp_cov(prices_input: str, span: int = 180, frequency: int = 252, log_returns: bool = False) -> str:
    """Calculate the annualized exponential covariance matrix."""
    df = _parse_prices(prices_input)
    S = risk_models.exp_cov(df, span=span, frequency=frequency, log_returns=log_returns)
    return _cov_to_json(S)

def ledoit_wolf(prices_input: str, shrinkage_target: str = "constant_variance") -> str:
    """Calculate the Ledoit-Wolf shrinkage estimate of the covariance matrix."""
    # target options: constant_variance, single_factor, constant_correlation
    df = _parse_prices(prices_input)
    if shrinkage_target == "constant_variance":
        S = risk_models.CovarianceShrinkage(df).ledoit_wolf(shrinkage_target='constant_variance')
    elif shrinkage_target == "single_factor":
        S = risk_models.CovarianceShrinkage(df).ledoit_wolf(shrinkage_target='single_factor')
    elif shrinkage_target == "constant_correlation":
        S = risk_models.CovarianceShrinkage(df).ledoit_wolf(shrinkage_target='constant_correlation')
    else:
        # Default fallback
        S = risk_models.CovarianceShrinkage(df).ledoit_wolf()
    return _cov_to_json(S)

def oracle_approximating(prices_input: str) -> str:
    """Calculate the Oracle Approximating Shrinkage estimate."""
    df = _parse_prices(prices_input)
    S = risk_models.CovarianceShrinkage(df).oracle_approximating()
    return _cov_to_json(S)
