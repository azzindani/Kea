from mcp_servers.quantstats_server.tools.core_ops import _parse_returns
import quantstats as qs
import pandas as pd
from typing import Dict, Any

def compare_alpha(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float:
    """Calculate Alpha vs Benchmark."""
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    return float(qs.stats.alpha(s, b, rf=risk_free))

def compare_beta(returns_input: str, benchmark_input: str = "SPY") -> float:
    """Calculate Beta vs Benchmark."""
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    return float(qs.stats.beta(s, b))

def compare_r_squared(returns_input: str, benchmark_input: str = "SPY") -> float:
    """Calculate R-Squared vs Benchmark."""
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    return float(qs.stats.r_squared(s, b))

def compare_correlation(returns_input: str, benchmark_input: str = "SPY") -> float:
    """Calculate Correlation vs Benchmark."""
    # qs.stats.correlation? Not explicitly in docs, uses pandas corr usually.
    # But qs.stats has it.
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    # Align dates
    df = pd.concat([s, b], axis=1).dropna()
    return float(df.iloc[:,0].corr(df.iloc[:,1]))

def compare_information_ratio(returns_input: str, benchmark_input: str = "SPY") -> float:
    """Information Ratio."""
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    return float(qs.stats.information_ratio(s, b))

def compare_treynor_ratio(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float:
    """Treynor Ratio."""
    s = _parse_returns(returns_input)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 10 else qs.utils.download_returns(benchmark_input)
    return float(qs.stats.treynor_ratio(s, b, rf=risk_free))
