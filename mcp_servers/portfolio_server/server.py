# /// script
# dependencies = [
#   "matplotlib",
#   "mcp",
#   "numpy",
#   "pandas",
#   "pyportfolioopt",
#   "scipy",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    core_ops, returns_ops, risk_ops, frontier_ops, 
    bl_ops, hrp_ops, allocation_ops, plotting_ops, super_ops
)
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("portfolio_server", dependencies=["pyportfolioopt", "pandas", "numpy", "matplotlib", "scipy"])

# ==========================================
# 1. Core & Data
# ==========================================
@mcp.tool()
def load_prices_csv(file_path: str) -> str: return core_ops.load_prices_csv(file_path)
@mcp.tool()
def validate_tickers(prices_input: str) -> dict: return core_ops.validate_tickers(prices_input)
@mcp.tool()
def get_latest_prices(prices_input: str) -> dict: return core_ops.get_latest_prices(prices_input)
@mcp.tool()
def calculate_returns(prices_input: str, log_returns: bool = False) -> str: return core_ops.calculate_returns(prices_input, log_returns)

# ==========================================
# 2. Expected Returns
# ==========================================
@mcp.tool()
def mean_historical_return(prices_input: str, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]: return returns_ops.mean_historical_return(prices_input, frequency, log_returns)
@mcp.tool()
def ema_historical_return(prices_input: str, span: int = 500, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]: return returns_ops.ema_historical_return(prices_input, span, frequency, log_returns)
@mcp.tool()
def capm_return(prices_input: str, market_prices_input: str = None, risk_free_rate: float = 0.02, frequency: int = 252) -> Dict[str, float]: return returns_ops.capm_return(prices_input, market_prices_input, risk_free_rate, frequency)

# ==========================================
# 3. Risk Models
# ==========================================
@mcp.tool()
def sample_cov(prices_input: str, frequency: int = 252, log_returns: bool = False) -> str: return risk_ops.sample_cov(prices_input, frequency, log_returns)
@mcp.tool()
def semicovariance(prices_input: str, benchmark: float = 0, frequency: int = 252, log_returns: bool = False) -> str: return risk_ops.semicovariance(prices_input, benchmark, frequency, log_returns)
@mcp.tool()
def exp_cov(prices_input: str, span: int = 180, frequency: int = 252, log_returns: bool = False) -> str: return risk_ops.exp_cov(prices_input, span, frequency, log_returns)
@mcp.tool()
def ledoit_wolf(prices_input: str, shrinkage_target: str = "constant_variance") -> str: return risk_ops.ledoit_wolf(prices_input, shrinkage_target)
@mcp.tool()
def oracle_approximating(prices_input: str) -> str: return risk_ops.oracle_approximating(prices_input)

# ==========================================
# 4. Frontier Optimization
# ==========================================
@mcp.tool()
def ef_max_sharpe(prices_input: str, risk_free_rate: float = 0.02) -> Dict[str, float]: return frontier_ops.ef_max_sharpe(prices_input, risk_free_rate)
@mcp.tool()
def ef_min_volatility(prices_input: str) -> Dict[str, float]: return frontier_ops.ef_min_volatility(prices_input)
@mcp.tool()
def ef_efficient_risk(prices_input: str, target_volatility: float) -> Dict[str, float]: return frontier_ops.ef_efficient_risk(prices_input, target_volatility)
@mcp.tool()
def ef_efficient_return(prices_input: str, target_return: float) -> Dict[str, float]: return frontier_ops.ef_efficient_return(prices_input, target_return)
@mcp.tool()
def ef_max_quadratic_utility(prices_input: str, risk_aversion: float = 1.0) -> Dict[str, float]: return frontier_ops.ef_max_quadratic_utility(prices_input, risk_aversion)
@mcp.tool()
def ef_portfolio_performance(prices_input: str, weights: Dict[str, float], risk_free_rate: float = 0.02) -> Dict[str, float]: return frontier_ops.ef_portfolio_performance(prices_input, weights, risk_free_rate)

# ==========================================
# 5. Black-Litterman
# ==========================================
@mcp.tool()
def bl_market_implied_risk_aversion(prices_input: str, risk_free_rate: float = 0.02) -> float: return bl_ops.bl_market_implied_risk_aversion(prices_input, risk_free_rate)
@mcp.tool()
def bl_compute_posterior(prices_input: str, absolute_views: Dict[str, float], risk_aversion: float = 1.0) -> Dict[str, Any]: return bl_ops.bl_compute_posterior(prices_input, absolute_views, risk_aversion)
@mcp.tool()
def bl_weights(prices_input: str, absolute_views: Dict[str, float]) -> Dict[str, float]: return bl_ops.bl_weights(prices_input, absolute_views)

# ==========================================
# 6. HRP
# ==========================================
@mcp.tool()
def hrp_optimize(prices_input: str) -> Dict[str, float]: return hrp_ops.hrp_optimize(prices_input)

# ==========================================
# 7. Allocation
# ==========================================
@mcp.tool()
def discrete_allocation_greedy(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]: return allocation_ops.discrete_allocation_greedy(prices_input, weights, total_portfolio_value)
@mcp.tool()
def discrete_allocation_lp(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]: return allocation_ops.discrete_allocation_lp(prices_input, weights, total_portfolio_value)
@mcp.tool()
def get_leftover_cash(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> float: return allocation_ops.get_leftover_cash(prices_input, weights, total_portfolio_value)

# ==========================================
# 8. Plotting
# ==========================================
@mcp.tool()
def plot_covariance(risk_matrix_input: str, plot_correlation: bool = False) -> str: return plotting_ops.plot_covariance(risk_matrix_input, plot_correlation)
@mcp.tool()
def plot_weights(weights: Dict[str, float]) -> str: return plotting_ops.plot_weights(weights)
@mcp.tool()
def plot_efficient_frontier(prices_input: str, points: int = 100) -> str: return plotting_ops.plot_efficient_frontier(prices_input, points)
@mcp.tool()
def plot_dendrogram(prices_input: str) -> str: return plotting_ops.plot_dendrogram(prices_input)

# ==========================================
# 9. Super Tools
# ==========================================
@mcp.tool()
def bulk_optimize_frontier(prices_input: str, risk_free_rate: float = 0.02) -> List[Dict[str, Any]]: return super_ops.bulk_optimize_frontier(prices_input, risk_free_rate)
@mcp.tool()
def optimize_portfolio_pipeline(prices_input: str, strategy: str = "max_sharpe", investment_amount: float = 10000.0) -> Dict[str, Any]: return super_ops.optimize_portfolio_pipeline(prices_input, strategy, investment_amount)
@mcp.tool()
def compare_risk_models(prices_input: str) -> Dict[str, Any]: return super_ops.compare_risk_models(prices_input)
@mcp.tool()
def generate_report(prices_input: str, weights: Dict[str, float]) -> str: return super_ops.generate_report(prices_input, weights)
@mcp.tool()
def parameter_sweep_gamma(prices_input: str, gammas: List[float] = [0.5, 1, 2, 5, 10]) -> List[Dict[str, Any]]: return super_ops.parameter_sweep_gamma(prices_input, gammas)
@mcp.tool()
def auto_rebalance(prices_input: str, current_holdings: Dict[str, int], target_strategy: str = "max_sharpe", total_value: float = None) -> Dict[str, Any]: return super_ops.auto_rebalance(prices_input, current_holdings, target_strategy, total_value)

if __name__ == "__main__":
    mcp.run()
