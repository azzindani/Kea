from mcp_servers.quantstats_server.tools.core_ops import download_returns, _parse_returns
import quantstats as qs
import pandas as pd
from typing import List, Dict, Any

def bulk_get_stats(tickers: List[str], period: str = "max") -> Dict[str, Dict[str, float]]:
    """Get key stats for multiple tickers."""
    # We could download all at once via yfinance if implemented, but qs utils is single
    # We will loop or use qs.utils.download_returns list logic if available
    # Iterate for now
    results = {}
    for t in tickers:
        try:
            s = qs.utils.download_returns(t, period=period)
            results[t] = {
                "sharpe": float(qs.stats.sharpe(s)),
                "cagr": float(qs.stats.cagr(s)),
                "volatility": float(qs.stats.volatility(s)),
                "max_drawdown": float(qs.stats.max_drawdown(s))
            }
        except Exception as e:
            results[t] = {"error": str(e)}
    return results

def bulk_compare_tickers(tickers: List[str], benchmark: str = "SPY", period: str = "max") -> Dict[str, Dict[str, float]]:
    """Compare multiple tickers against a benchmark."""
    try:
        b = qs.utils.download_returns(benchmark, period=period)
    except:
        b = None
        
    results = {}
    for t in tickers:
        try:
            s = qs.utils.download_returns(t, period=period)
            results[t] = {
                "alpha": float(qs.stats.alpha(s, b)) if b is not None else None,
                "beta": float(qs.stats.beta(s, b)) if b is not None else None,
                "correlation": float(qs.stats.pearson(s, b)) if b is not None else None, # using pearson alias? or pandas corr
                 # QS stats often rely on alignment
                 "r_squared": float(qs.stats.r_squared(s, b)) if b is not None else None
            }
        except Exception as e:
            results[t] = {"error": str(e)}
    return results
