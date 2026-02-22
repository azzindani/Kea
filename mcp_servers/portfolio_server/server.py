
import sys
import os
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Clear MPLBACKEND before importing matplotlib (Kaggle sets invalid value)
os.environ.pop('MPLBACKEND', None)

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.portfolio_server.tools import (
    core_ops, returns_ops, risk_ops, frontier_ops, 
    bl_ops, hrp_ops, allocation_ops, plotting_ops, super_ops
)
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("portfolio_server", dependencies=["pyportfolioopt", "pandas", "numpy", "matplotlib", "scipy"])

# ==========================================
# 1. Core & Data
# ==========================================
# ==========================================
# 1. Core & Data
# ==========================================
@mcp.tool()
def load_prices_csv(file_path: str) -> str: 
    """LOADS prices. [ACTION]
    
    [RAG Context]
    Load price data from CSV file.
    Returns JSON string of prices.
    """
    return core_ops.load_prices_csv(file_path)

@mcp.tool()
def validate_tickers(prices_input: str) -> dict: 
    """VALIDATES tickers. [ACTION]
    
    [RAG Context]
    Check if tickers in price data are valid.
    Returns validation report.
    """
    return core_ops.validate_tickers(prices_input)

@mcp.tool()
def get_latest_prices(prices_input: str) -> dict: 
    """FETCHES latest prices. [ACTION]
    
    [RAG Context]
    Get the most recent price for each asset.
    Returns dict of ticker->price.
    """
    return core_ops.get_latest_prices(prices_input)

@mcp.tool()
def calculate_returns(prices_input: str, log_returns: bool = False) -> str: 
    """CALCULATES returns. [ACTION]
    
    [RAG Context]
    Compute historical returns from prices.
    Returns JSON string of returns.
    """
    return core_ops.calculate_returns(prices_input, log_returns)

# ==========================================
# 2. Expected Returns
# ==========================================
@mcp.tool()
def mean_historical_return(prices_input: str, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]: 
    """CALCULATES mean return. [ACTION]
    
    [RAG Context]
    Calculate annualized mean historical return.
    Returns dict of ticker->return.
    """
    return returns_ops.mean_historical_return(prices_input, frequency, log_returns)

@mcp.tool()
def ema_historical_return(prices_input: str, span: int = 500, frequency: int = 252, log_returns: bool = False) -> Dict[str, float]: 
    """CALCULATES EMA return. [ACTION]
    
    [RAG Context]
    Calculate exponential moving average return.
    Returns dict of ticker->return.
    """
    return returns_ops.ema_historical_return(prices_input, span, frequency, log_returns)

@mcp.tool()
def capm_return(prices_input: str, market_prices_input: str = None, risk_free_rate: float = 0.02, frequency: int = 252) -> Dict[str, float]: 
    """CALCULATES CAPM. [ACTION]
    
    [RAG Context]
    Calculate expected return using CAPM model.
    Returns dict of ticker->return.
    """
    return returns_ops.capm_return(prices_input, market_prices_input, risk_free_rate, frequency)

# ==========================================
# 3. Risk Models
# ==========================================
@mcp.tool()
def sample_cov(prices_input: str, frequency: int = 252, log_returns: bool = False) -> str: 
    """CALCULATES sample cov. [ACTION]
    
    [RAG Context]
    Calculate sample covariance matrix.
    Returns JSON string of matrix.
    """
    return risk_ops.sample_cov(prices_input, frequency, log_returns)

@mcp.tool()
def semicovariance(prices_input: str, benchmark: float = 0, frequency: int = 252, log_returns: bool = False) -> str: 
    """CALCULATES semicovariance. [ACTION]
    
    [RAG Context]
    Calculate semicovariance matrix (downside risk).
    Returns JSON string of matrix.
    """
    return risk_ops.semicovariance(prices_input, benchmark, frequency, log_returns)

@mcp.tool()
def exp_cov(prices_input: str, span: int = 180, frequency: int = 252, log_returns: bool = False) -> str: 
    """CALCULATES exp cov. [ACTION]
    
    [RAG Context]
    Calculate exponential covariance matrix.
    Returns JSON string of matrix.
    """
    return risk_ops.exp_cov(prices_input, span, frequency, log_returns)

@mcp.tool()
def ledoit_wolf(prices_input: str, shrinkage_target: str = "constant_variance") -> str: 
    """CALCULATES Ledoit-Wolf. [ACTION]
    
    [RAG Context]
    Calculate Ledoit-Wolf shrinkage covariance.
    Returns JSON string of matrix.
    """
    return risk_ops.ledoit_wolf(prices_input, shrinkage_target)

@mcp.tool()
def oracle_approximating(prices_input: str) -> str: 
    """CALCULATES oracle. [ACTION]
    
    [RAG Context]
    Calculate Oracle Approximating shrinkage covariance.
    Returns JSON string of matrix.
    """
    return risk_ops.oracle_approximating(prices_input)

# ==========================================
# 4. Frontier Optimization
# ==========================================
# ==========================================
# 4. Frontier Optimization
# ==========================================
@mcp.tool()
def ef_max_sharpe(prices_input: str, risk_free_rate: float = 0.02) -> Dict[str, float]: 
    """OPTIMIZES Sharpe. [ACTION]
    
    [RAG Context]
    Optimize portfolio for maximum Sharpe ratio.
    Returns dict of weights.
    """
    return frontier_ops.ef_max_sharpe(prices_input, risk_free_rate)

@mcp.tool()
def ef_min_volatility(prices_input: str) -> Dict[str, float]: 
    """OPTIMIZES volatility. [ACTION]
    
    [RAG Context]
    Optimize portfolio for minimum volatility.
    Returns dict of weights.
    """
    return frontier_ops.ef_min_volatility(prices_input)

@mcp.tool()
def ef_efficient_risk(prices_input: str, target_volatility: float) -> Dict[str, float]: 
    """OPTIMIZES target risk. [ACTION]
    
    [RAG Context]
    Maximize return for a given target volatility.
    Returns dict of weights.
    """
    return frontier_ops.ef_efficient_risk(prices_input, target_volatility)

@mcp.tool()
def ef_efficient_return(prices_input: str, target_return: float) -> Dict[str, float]: 
    """OPTIMIZES target return. [ACTION]
    
    [RAG Context]
    Minimize risk for a given target return.
    Returns dict of weights.
    """
    return frontier_ops.ef_efficient_return(prices_input, target_return)

@mcp.tool()
def ef_max_quadratic_utility(prices_input: str, risk_aversion: float = 1.0) -> Dict[str, float]: 
    """OPTIMIZES utility. [ACTION]
    
    [RAG Context]
    Maximize quadratic utility given risk aversion.
    Returns dict of weights.
    """
    return frontier_ops.ef_max_quadratic_utility(prices_input, risk_aversion)

@mcp.tool()
def ef_portfolio_performance(prices_input: str, weights: Dict[str, float], risk_free_rate: float = 0.02) -> Dict[str, float]: 
    """CALCULATES performance. [ACTION]
    
    [RAG Context]
    Calculate expected return, volatility, and Sharpe of portfolio.
    Returns dict of metrics.
    """
    return frontier_ops.ef_portfolio_performance(prices_input, weights, risk_free_rate)

# ==========================================
# 5. Black-Litterman
# ==========================================
@mcp.tool()
def bl_market_implied_risk_aversion(prices_input: str, risk_free_rate: float = 0.02) -> float: 
    """CALCULATES lambda. [ACTION]
    
    [RAG Context]
    Calculate market-implied risk aversion parameter.
    Returns float.
    """
    return bl_ops.bl_market_implied_risk_aversion(prices_input, risk_free_rate)

@mcp.tool()
def bl_compute_posterior(prices_input: str, absolute_views: Dict[str, float], risk_aversion: float = 1.0) -> Dict[str, Any]: 
    """CALCULATES posterior. [ACTION]
    
    [RAG Context]
    Compute posterior expected returns and covariance (BL model).
    Returns JSON dict.
    """
    return bl_ops.bl_compute_posterior(prices_input, absolute_views, risk_aversion)

@mcp.tool()
def bl_weights(prices_input: str, absolute_views: Dict[str, float]) -> Dict[str, float]: 
    """OPTIMIZES BL weights. [ACTION]
    
    [RAG Context]
    Optimize portfolio using Black-Litterman model.
    Returns dict of weights.
    """
    return bl_ops.bl_weights(prices_input, absolute_views)

# ==========================================
# 6. HRP
# ==========================================
@mcp.tool()
def hrp_optimize(prices_input: str) -> Dict[str, float]: 
    """OPTIMIZES HRP. [ACTION]
    
    [RAG Context]
    Optimize using Hierarchical Risk Parity.
    Returns dict of weights.
    """
    return hrp_ops.hrp_optimize(prices_input)

# ==========================================
# 7. Allocation
# ==========================================
# ==========================================
# 7. Allocation
# ==========================================
@mcp.tool()
def discrete_allocation_greedy(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]: 
    """ALLOCATES greedy. [ACTION]
    
    [RAG Context]
    Calculate discrete allocation (shares) using greedy algorithm.
    Returns dict of allocation info.
    """
    return allocation_ops.discrete_allocation_greedy(prices_input, weights, total_portfolio_value)

@mcp.tool()
def discrete_allocation_lp(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> Dict[str, Any]: 
    """ALLOCATES linear prog. [ACTION]
    
    [RAG Context]
    Calculate discrete allocation (shares) using linear programming.
    Returns dict of allocation.
    """
    return allocation_ops.discrete_allocation_lp(prices_input, weights, total_portfolio_value)

@mcp.tool()
def get_leftover_cash(prices_input: str, weights: Dict[str, float], total_portfolio_value: float = 10000.0) -> float: 
    """CALCULATES leftover. [ACTION]
    
    [RAG Context]
    Calculate unallocated cash after discrete allocation.
    Returns float amount.
    """
    return allocation_ops.get_leftover_cash(prices_input, weights, total_portfolio_value)

# ==========================================
# 8. Plotting
# ==========================================
@mcp.tool()
def plot_covariance(risk_matrix_input: str, plot_correlation: bool = False) -> str: 
    """PLOTS covariance. [ACTION]
    
    [RAG Context]
    Generate heatmap of covariance/correlation matrix.
    Returns plot image path.
    """
    return plotting_ops.plot_covariance(risk_matrix_input, plot_correlation)

@mcp.tool()
def plot_weights(weights: Dict[str, float]) -> str: 
    """PLOTS weights. [ACTION]
    
    [RAG Context]
    Generate bar chart of portfolio weights.
    Returns plot image path.
    """
    return plotting_ops.plot_weights(weights)

@mcp.tool()
def plot_efficient_frontier(prices_input: str, points: int = 100) -> str: 
    """PLOTS frontier. [ACTION]
    
    [RAG Context]
    Plot efficient frontier curve.
    Returns plot image path.
    """
    return plotting_ops.plot_efficient_frontier(prices_input, points)

@mcp.tool()
def plot_dendrogram(prices_input: str) -> str: 
    """PLOTS dendrogram. [ACTION]
    
    [RAG Context]
    Generate clustering dendrogram for assets.
    Returns plot image path.
    """
    return plotting_ops.plot_dendrogram(prices_input)

# ==========================================
# 9. Super Tools
# ==========================================
@mcp.tool()
def bulk_optimize_frontier(prices_input: str, risk_free_rate: float = 0.02) -> List[Dict[str, Any]]: 
    """BULK: Optimize Frontier. [ACTION]
    
    [RAG Context]
    Compute multiple frontier portfolios (min vol, max sharpe, etc).
    Returns list of portfolios.
    """
    return super_ops.bulk_optimize_frontier(prices_input, risk_free_rate)

@mcp.tool()
def optimize_portfolio_pipeline(prices_input: str, strategy: str = "max_sharpe", investment_amount: float = 10000.0) -> Dict[str, Any]: 
    """PIPELINE: Optimize. [ACTION]
    
    [RAG Context]
    End-to-end portfolio optimization and allocation.
    Returns comprehensive result dict.
    """
    return super_ops.optimize_portfolio_pipeline(prices_input, strategy, investment_amount)

@mcp.tool()
def compare_risk_models(prices_input: str) -> Dict[str, Any]: 
    """COMPARES risk. [ACTION]
    
    [RAG Context]
    Compare different covariance estimation methods.
    Returns comparison dict.
    """
    return super_ops.compare_risk_models(prices_input)

@mcp.tool()
def generate_report(prices_input: str, weights: Dict[str, float]) -> str: 
    """GENERATES report. [ACTION]
    
    [RAG Context]
    Create detailed PDF/Markdown portfolio report.
    Returns file path.
    """
    return super_ops.generate_report(prices_input, weights)

@mcp.tool()
def parameter_sweep_gamma(prices_input: str, gammas: List[float] = [0.5, 1, 2, 5, 10]) -> List[Dict[str, Any]]: 
    """SWEEPS gamma. [ACTION]
    
    [RAG Context]
    Analyze impact of risk aversion parameter.
    Returns list of results.
    """
    return super_ops.parameter_sweep_gamma(prices_input, gammas)

@mcp.tool()
def auto_rebalance(prices_input: str, current_holdings: Dict[str, int], target_strategy: str = "max_sharpe", total_value: float = None) -> Dict[str, Any]: 
    """REBALANCES portfolio. [ACTION]
    
    [RAG Context]
    Calculate trades needed to match target strategy.
    Returns trade instructions.
    """
    return super_ops.auto_rebalance(prices_input, current_holdings, target_strategy, total_value)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PortfolioServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

