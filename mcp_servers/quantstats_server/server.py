from mcp.server.fastmcp import FastMCP
from mcp_servers.quantstats_server.tools import (
    core_ops, stats_ops, risk_ops, compare_ops, 
    plot_ops, report_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("quantstats_server", dependencies=["quantstats", "pandas", "matplotlib", "seaborn", "yfinance"])

# ==========================================
# 1. Core & Data
# ==========================================
@mcp.tool()
def download_returns(ticker: str, period: str = "max") -> str: return core_ops.download_returns(ticker, period)
@mcp.tool()
def load_returns_csv(file_path: str) -> str: return core_ops.load_returns_csv(file_path)
@mcp.tool()
def make_index(returns_input: str, initial_value: float = 100.0) -> str: return core_ops.make_index(returns_input, initial_value)

# ==========================================
# 2. Statistics
# ==========================================
@mcp.tool()
def stats_cagr(returns_input: str, risk_free: float = 0.0) -> float: return stats_ops.stats_cagr(returns_input, risk_free)
@mcp.tool()
def stats_sharpe(returns_input: str, risk_free: float = 0.0) -> float: return stats_ops.stats_sharpe(returns_input, risk_free)
@mcp.tool()
def stats_sortino(returns_input: str, risk_free: float = 0.0) -> float: return stats_ops.stats_sortino(returns_input, risk_free)
@mcp.tool()
def stats_calmar(returns_input: str) -> float: return stats_ops.stats_calmar(returns_input)
@mcp.tool()
def stats_omega(returns_input: str, risk_free: float = 0.0) -> float: return stats_ops.stats_omega(returns_input, risk_free)
@mcp.tool()
def stats_win_rate(returns_input: str) -> float: return stats_ops.stats_win_rate(returns_input)
@mcp.tool()
def stats_profit_factor(returns_input: str) -> float: return stats_ops.stats_profit_factor(returns_input)
@mcp.tool()
def stats_avg_return(returns_input: str) -> float: return stats_ops.stats_avg_return(returns_input)
@mcp.tool()
def stats_avg_win(returns_input: str) -> float: return stats_ops.stats_avg_win(returns_input)
@mcp.tool()
def stats_avg_loss(returns_input: str) -> float: return stats_ops.stats_avg_loss(returns_input)
@mcp.tool()
def stats_comp(returns_input: str) -> float: return stats_ops.stats_comp(returns_input)
@mcp.tool()
def stats_kelly_criterion(returns_input: str) -> float: return stats_ops.stats_kelly_criterion(returns_input)
@mcp.tool()
def stats_payoff_ratio(returns_input: str) -> float: return stats_ops.stats_payoff_ratio(returns_input)
@mcp.tool()
def stats_common_sense_ratio(returns_input: str) -> float: return stats_ops.stats_common_sense_ratio(returns_input)
@mcp.tool()
def stats_expectancy(returns_input: str) -> float: return stats_ops.stats_expectancy(returns_input)

# ==========================================
# 3. Risk
# ==========================================
@mcp.tool()
def risk_max_drawdown(returns_input: str) -> float: return risk_ops.risk_max_drawdown(returns_input)
@mcp.tool()
def risk_avg_drawdown(returns_input: str) -> float: return risk_ops.risk_avg_drawdown(returns_input)
@mcp.tool()
def risk_volatility(returns_input: str) -> float: return risk_ops.risk_volatility(returns_input)
@mcp.tool()
def risk_var(returns_input: str, sigma: float = 1.0) -> float: return risk_ops.risk_var(returns_input, sigma)
@mcp.tool()
def risk_cvar(returns_input: str, sigma: float = 1.0) -> float: return risk_ops.risk_cvar(returns_input, sigma)
@mcp.tool()
def risk_skew(returns_input: str) -> float: return risk_ops.risk_skew(returns_input)
@mcp.tool()
def risk_kurtosis(returns_input: str) -> float: return risk_ops.risk_kurtosis(returns_input)
@mcp.tool()
def risk_ulcer_index(returns_input: str) -> float: return risk_ops.risk_ulcer_index(returns_input)
@mcp.tool()
def risk_serenity_index(returns_input: str, risk_free: float = 0.0) -> float: return risk_ops.risk_serenity_index(returns_input, risk_free)
@mcp.tool()
def risk_tail_ratio(returns_input: str) -> float: return risk_ops.risk_tail_ratio(returns_input)
@mcp.tool()
def risk_risk_return_ratio(returns_input: str) -> float: return risk_ops.risk_risk_return_ratio(returns_input)

# ==========================================
# 4. Comparative
# ==========================================
@mcp.tool()
def compare_alpha(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float: return compare_ops.compare_alpha(returns_input, benchmark_input, risk_free)
@mcp.tool()
def compare_beta(returns_input: str, benchmark_input: str = "SPY") -> float: return compare_ops.compare_beta(returns_input, benchmark_input)
@mcp.tool()
def compare_r_squared(returns_input: str, benchmark_input: str = "SPY") -> float: return compare_ops.compare_r_squared(returns_input, benchmark_input)
@mcp.tool()
def compare_correlation(returns_input: str, benchmark_input: str = "SPY") -> float: return compare_ops.compare_correlation(returns_input, benchmark_input)
@mcp.tool()
def compare_information_ratio(returns_input: str, benchmark_input: str = "SPY") -> float: return compare_ops.compare_information_ratio(returns_input, benchmark_input)
@mcp.tool()
def compare_treynor_ratio(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float: return compare_ops.compare_treynor_ratio(returns_input, benchmark_input, risk_free)

# ==========================================
# 5. Plotting
# ==========================================
@mcp.tool()
def plot_snapshot(returns_input: str, title: str = "Performance Snapshot") -> str: return plot_ops.plot_snapshot(returns_input, title)
@mcp.tool()
def plot_cumulative_returns(returns_input: str, benchmark_input: str = None) -> str: return plot_ops.plot_cumulative_returns(returns_input, benchmark_input)
@mcp.tool()
def plot_drawdown(returns_input: str) -> str: return plot_ops.plot_drawdown(returns_input)
@mcp.tool()
def plot_daily_returns(returns_input: str) -> str: return plot_ops.plot_daily_returns(returns_input)
@mcp.tool()
def plot_monthly_heatmap(returns_input: str) -> str: return plot_ops.plot_monthly_heatmap(returns_input)
@mcp.tool()
def plot_distribution(returns_input: str) -> str: return plot_ops.plot_distribution(returns_input)
@mcp.tool()
def plot_rolling_sharpe(returns_input: str, periods: int = 126) -> str: return plot_ops.plot_rolling_sharpe(returns_input, periods)
@mcp.tool()
def plot_rolling_volatility(returns_input: str, periods: int = 126) -> str: return plot_ops.plot_rolling_volatility(returns_input, periods)
@mcp.tool()
def plot_rolling_beta(returns_input: str, benchmark_input: str = "SPY", periods: int = 126) -> str: return plot_ops.plot_rolling_beta(returns_input, benchmark_input, periods)

# ==========================================
# 6. Reports
# ==========================================
@mcp.tool()
def report_html(returns_input: str, benchmark_input: str = None, title: str = "Strategy Report") -> str: return report_ops.report_html(returns_input, benchmark_input, title)
@mcp.tool()
def report_metrics(returns_input: str, benchmark_input: str = None) -> str: return report_ops.report_metrics(returns_input, benchmark_input)
@mcp.tool()
def report_full(returns_input: str) -> str: return report_ops.report_full(returns_input)

# ==========================================
# 7. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_get_stats(tickers: List[str], period: str = "max") -> Dict[str, Dict[str, float]]: return bulk_ops.bulk_get_stats(tickers, period)
@mcp.tool()
def bulk_compare_tickers(tickers: List[str], benchmark: str = "SPY", period: str = "max") -> Dict[str, Dict[str, float]]: return bulk_ops.bulk_compare_tickers(tickers, benchmark, period)

@mcp.tool()
def super_tearsheet(returns_input: str, benchmark_input: str = "SPY", title: str = "Analysis") -> Dict[str, Any]: return super_ops.super_tearsheet(returns_input, benchmark_input, title)
@mcp.tool()
def diagnose_strategy(returns_input: str) -> Dict[str, Any]: return super_ops.diagnose_strategy(returns_input)
@mcp.tool()
def rolling_stats_dataframe(returns_input: str, window: int = 126) -> str: return super_ops.rolling_stats_dataframe(returns_input, window)

if __name__ == "__main__":
    mcp.run()
