from mcp_servers.quantstats_server.tools.core_ops import _parse_returns, safe_float
import quantstats as qs
from typing import Dict, Any

def risk_max_drawdown(returns_input: str) -> float:
    """Maximum Drawdown."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.max_drawdown(s))

def risk_avg_drawdown(returns_input: str) -> float:
    """Average Drawdown."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.avg_drawdown(s))

def risk_volatility(returns_input: str) -> float:
    """Annualized Volatility."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.volatility(s))

def risk_var(returns_input: str, sigma: float = 1.0) -> float:
    """Value at Risk."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.var(s, sigma=sigma))

def risk_cvar(returns_input: str, sigma: float = 1.0) -> float:
    """Conditional Value at Risk."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.cvar(s, sigma=sigma))

def risk_skew(returns_input: str) -> float:
    """Skewness."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.skew(s))

def risk_kurtosis(returns_input: str) -> float:
    """Kurtosis."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.kurtosis(s))

def risk_ulcer_index(returns_input: str) -> float:
    """Ulcer Index."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.ulcer_index(s))

def risk_serenity_index(returns_input: str, risk_free: float = 0.0) -> float:
    """Serenity Index."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.serenity_index(s, rf=risk_free))

def risk_tail_ratio(returns_input: str) -> float:
    """Tail Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.tail_ratio(s))

def risk_risk_return_ratio(returns_input: str) -> float:
    """Risk/Return Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.risk_return_ratio(s))
