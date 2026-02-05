from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import discrete_allocation
import pandas as pd
from typing import Dict, Any, Tuple

def _get_allocation(prices_input: str, weights: Dict[str, float], total_portfolio_value: float, method: str = "greedy") -> Tuple[Dict[str, int], float]:
    df = _parse_prices(prices_input)
    latest_prices = df.iloc[-1]
    
    da = discrete_allocation.DiscreteAllocation(weights, latest_prices, total_portfolio_value=total_portfolio_value)
    
    if method == "lp":
        allocation, leftover = da.lp_portfolio()
    else:
        allocation, leftover = da.greedy_portfolio()
    return allocation, leftover

def discrete_allocation_greedy(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]:
    """Convert continuous weights to integer shares using Greedy algorithm."""
    allocation, leftover = _get_allocation(prices_input, weights, total_portfolio_value, "greedy")
    return {
        "allocation": allocation,
        "leftover_cash": float(leftover)
    }

def discrete_allocation_lp(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]:
    """Convert continuous weights to integer shares using Linear Programming (exact)."""
    # Note: LP requires cvxpy installed.
    allocation, leftover = _get_allocation(prices_input, weights, total_portfolio_value, "lp")
    return {
        "allocation": allocation,
        "leftover_cash": float(leftover)
    }

def get_leftover_cash(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> float:
    """Calculate just the leftover cash from a greedy allocation."""
    _, leftover = _get_allocation(prices_input, weights, total_portfolio_value, "greedy")
    return float(leftover)
