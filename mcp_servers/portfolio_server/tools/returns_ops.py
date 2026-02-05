from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import expected_returns
import pandas as pd
from typing import Dict, Any

def mean_historical_return(prices_input: str, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]:
    """Calculate the annualized mean historical return."""
    df = _parse_prices(prices_input)
    mu = expected_returns.mean_historical_return(df, frequency=frequency, log_returns=log_returns)
    return mu.to_dict()

def ema_historical_return(prices_input: str, span: int = 500, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]:
    """Calculate the annualized exponential moving average return."""
    df = _parse_prices(prices_input)
    mu = expected_returns.ema_historical_return(df, frequency=frequency, span=span, log_returns=log_returns)
    return mu.to_dict()

def capm_return(prices_input: str, market_prices_input: str = None, risk_free_rate: float = 0.02, frequency: int = 252) -> Dict[str, float]:
    """Calculate the expected return using CATM."""
    df = _parse_prices(prices_input)
    market_df = _parse_prices(market_prices_input) if market_prices_input else None
    mu = expected_returns.capm_return(df, market_prices=market_df, risk_free_rate=risk_free_rate, frequency=frequency)
    return mu.to_dict()

def returns_from_prices(prices_input: str) -> str:
    """Get simple percent returns DataFrame (helper for other tools)."""
    df = _parse_prices(prices_input)
    return expected_returns.returns_from_prices(df).to_json(orient='split', date_format='iso')
