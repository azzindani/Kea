from mcp_servers.portfolio_server.tools import core_ops, returns_ops, risk_ops, frontier_ops, bl_ops, hrp_ops, allocation_ops
from pypfopt import expected_returns, risk_models
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def bulk_optimize_frontier(prices_input: str, risk_free_rate: float = 0.02) -> List[Dict[str, Any]]:
    """Verify multiple strategies at once: Max Sharpe, Min Volatility, HRP."""
    res = []
    
    # Max Sharpe
    try:
        w_sharpe = frontier_ops.ef_max_sharpe(prices_input, risk_free_rate)
        perf_sharpe = frontier_ops.ef_portfolio_performance(prices_input, w_sharpe, risk_free_rate)
        res.append({"strategy": "Max Sharpe", "weights": w_sharpe, "performance": perf_sharpe})
    except Exception as e:
        res.append({"strategy": "Max Sharpe", "error": str(e)})

    # Min Vol
    try:
        w_minvol = frontier_ops.ef_min_volatility(prices_input)
        perf_minvol = frontier_ops.ef_portfolio_performance(prices_input, w_minvol, risk_free_rate)
        res.append({"strategy": "Min Volatility", "weights": w_minvol, "performance": perf_minvol})
    except Exception as e:
        res.append({"strategy": "Min Volatility", "error": str(e)})
        
    # HRP
    try:
         w_hrp = hrp_ops.hrp_optimize(prices_input)
         perf_hrp = frontier_ops.ef_portfolio_performance(prices_input, w_hrp, risk_free_rate)
         res.append({"strategy": "HRP", "weights": w_hrp, "performance": perf_hrp})
    except Exception as e:
         res.append({"strategy": "HRP", "error": str(e)})
         
    return res

def optimize_portfolio_pipeline(prices_input: str, strategy: str = "max_sharpe", investment_amount: float = 10000.0) -> Dict[str, Any]:
    """End-to-End Pipeline: Prices -> Optimize -> Discrete Allocation."""
    if strategy == "max_sharpe":
        weights = frontier_ops.ef_max_sharpe(prices_input)
    elif strategy == "min_volatility":
        weights = frontier_ops.ef_min_volatility(prices_input)
    elif strategy == "hrp":
        weights = hrp_ops.hrp_optimize(prices_input)
    else:
        return {"error": "Unknown strategy"}
        
    alloc_res = allocation_ops.discrete_allocation_greedy(prices_input, weights, investment_amount)
    
    return {
        "strategy": strategy,
        "continuous_weights": weights,
        "discrete_allocation": alloc_res['allocation'],
        "leftover_cash": alloc_res['leftover_cash']
    }

def compare_risk_models(prices_input: str) -> Dict[str, Any]:
    """Compute and compare multiple covariance matrices."""
    # We will return the condition number/trace as summary stats? 
    # Or just returning them all might be heavy.
    # Let's return summary stats: Condition Number (stability)
    df = core_ops._parse_prices(prices_input)
    
    models = {
        "sample": risk_models.sample_cov(df),
        "semicovariance": risk_models.semicovariance(df),
        "exp": risk_models.exp_cov(df),
        "ledoit_wolf": risk_models.CovarianceShrinkage(df).ledoit_wolf(),
        "oracle": risk_models.CovarianceShrinkage(df).oracle_approximating()
    }
    
    stats = {}
    for name, cov in models.items():
        cond_num = np.linalg.cond(cov)
        stats[name] = {
            "condition_number": cond_num,
            "trace": np.trace(cov),
            "max_var": cov.max().max()
        }
    return stats

def generate_report(prices_input: str, weights: Dict[str, float]) -> str:
    """Generate a Markdown report of the portfolio."""
    perf = frontier_ops.ef_portfolio_performance(prices_input, weights)
    
    report = f"""
# Portfolio Performance Report

## Metrics
- **Expected Annual Return**: {perf['expected_return']:.2%}
- **Annual Volatility**: {perf['volatility']:.2%}
- **Sharpe Ratio**: {perf['sharpe_ratio']:.2f}

## Composition
    """
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    for asset, w in sorted_weights:
        if w > 0.001:
            report += f"- **{asset}**: {w:.2%}\n"
            
    return report

def parameter_sweep_gamma(prices_input: str, gammas: List[float] = [0.5, 1, 2, 5, 10]) -> List[Dict[str, Any]]:
    """Sweep risk aversion (gamma) for Max Quadratic Utility."""
    results = []
    for g in gammas:
        w = frontier_ops.ef_max_quadratic_utility(prices_input, risk_aversion=g)
        perf = frontier_ops.ef_portfolio_performance(prices_input, w)
        results.append({"gamma": g, "performance": perf, "weights": w})
    return results

def auto_rebalance(prices_input: str, current_holdings: Dict[str, int], target_strategy: str = "max_sharpe", total_value: float = None) -> Dict[str, Any]:
    """Calculate trades needed to reach target strategy from current holdings."""
    # 1. Get current value
    df = core_ops._parse_prices(prices_input)
    latest_prices = df.iloc[-1]
    
    current_value = sum(hist_qty * latest_prices[ticker] for ticker, hist_qty in current_holdings.items() if ticker in latest_prices)
    if total_value is None: total_value = current_value
    
    # 2. Get target weights
    if target_strategy == "max_sharpe":
        target_w = frontier_ops.ef_max_sharpe(prices_input)
    elif target_strategy == "min_volatility":
        target_w = frontier_ops.ef_min_volatility(prices_input)
    else:
        return {"error": "Strategy not supported"}
        
    # 3. Get target allocation
    alloc_res = allocation_ops.discrete_allocation_greedy(prices_input, target_w, total_value)
    target_holdings = alloc_res['allocation']
    
    # 4. Diff
    trades = {}
    all_tickers = set(current_holdings.keys()) | set(target_holdings.keys())
    for t in all_tickers:
        curr = current_holdings.get(t, 0)
        tgt = target_holdings.get(t, 0)
        diff = tgt - curr
        if diff != 0:
            trades[t] = diff
            
    return {
        "current_value": current_value,
        "target_value": total_value,
        "trades_needed": trades,
        "target_holdings": target_holdings
    }
