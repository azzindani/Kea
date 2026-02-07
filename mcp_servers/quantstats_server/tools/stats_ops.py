from mcp_servers.quantstats_server.tools.core_ops import _parse_returns, safe_float
import quantstats as qs
import pandas as pd
from typing import Dict, Any, Union

# Common default RF
RISK_FREE = 0.0

def stats_cagr(returns_input: str, risk_free: float = RISK_FREE) -> float:
    """Compound Annual Growth Rate."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.cagr(s, rf=risk_free))

def stats_sharpe(returns_input: str, risk_free: float = RISK_FREE) -> float:
    """Sharpe Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.sharpe(s, rf=risk_free))

def stats_sortino(returns_input: str, risk_free: float = RISK_FREE) -> float:
    """Sortino Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.sortino(s, rf=risk_free))

def stats_calmar(returns_input: str) -> float:
    """Calmar Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.calmar(s))

def stats_omega(returns_input: str, risk_free: float = RISK_FREE) -> float:
    """Omega Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.omega(s, rf=risk_free))

def stats_win_rate(returns_input: str) -> float:
    """Win Rate (%)."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.win_rate(s))

def stats_profit_factor(returns_input: str) -> float:
    """Profit Factor."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.profit_factor(s))

def stats_avg_return(returns_input: str) -> float:
    """Average Return."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.avg_return(s))

def stats_avg_win(returns_input: str) -> float:
    """Average Win."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.avg_win(s))

def stats_avg_loss(returns_input: str) -> float:
    """Average Loss."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.avg_loss(s))

def stats_comp(returns_input: str) -> float:
    """Compound Returns (Total Return)."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.comp(s))

def stats_kelly_criterion(returns_input: str) -> float:
    """Kelly Criterion."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.kelly_criterion(s))

def stats_payoff_ratio(returns_input: str) -> float:
    """Payoff Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.payoff_ratio(s))

def stats_common_sense_ratio(returns_input: str) -> float:
    """Common Sense Ratio."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.common_sense_ratio(s))

def stats_expectancy(returns_input: str) -> float:
    """Expectancy."""
    s = _parse_returns(returns_input)
    return safe_float(qs.stats.expectancy(s))
