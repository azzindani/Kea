
import sys
import os
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Clear MPLBACKEND before importing matplotlib (Kaggle sets invalid value)
os.environ.pop('MPLBACKEND', None)
import matplotlib
matplotlib.use("Agg")

import logging
# Suppress font manager warnings (e.g., "Arial not found")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", message=".*font family.*not found.*")

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.quantstats_server.tools import (
    core_ops, stats_ops, risk_ops, compare_ops, 
    plot_ops, report_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("quantstats_server", dependencies=["quantstats", "pandas", "matplotlib", "seaborn", "yfinance"])

# ==========================================
# 1. Core & Data
# ==========================================
@mcp.tool()
def download_returns(ticker: str, period: str = "max") -> str: 
    """FETCHES returns. [ACTION]
    
    [RAG Context]
    A data acquisition "Super Tool" for quantitative finance. It retrieves historical price data for a given ticker and automatically transforms it into a daily returns time-series.
    
    How to Use:
    - 'ticker': Ticker symbol (e.g., 'AAPL', 'BTC-USD', 'GC=F').
    - 'period': Valid Yahoo Finance periods (e.g., '1y', '5y', 'max').
    - Returns a JSON string representing a pandas Series of percent changes.
    
    Keywords: returns fetcher, price to returns, quant data, ticker history.
    """
    return core_ops.download_returns(ticker, period)

@mcp.tool()
def load_returns_csv(file_path: str) -> str: 
    """LOADS returns from CSV. [ACTION]
    
    [RAG Context]
    Loads returns data from a CSV file.
    Returns JSON string.
    """
    return core_ops.load_returns_csv(file_path)

@mcp.tool()
def make_index(returns_input: str, initial_value: float = 100.0) -> str: 
    """CALCULATES index. [ACTION]
    
    [RAG Context]
    Converts returns to a price index (init 100).
    Returns JSON string.
    """
    return core_ops.make_index(returns_input, initial_value)

# ==========================================
# 2. Statistics
# ==========================================
@mcp.tool()
def stats_cagr(returns_input: str, risk_free: float = 0.0) -> float: 
    """CALCULATES CAGR. [ACTION]
    
    [RAG Context]
    Compound Annual Growth Rate.
    Returns float.
    """
    return stats_ops.stats_cagr(returns_input, risk_free)

@mcp.tool()
def stats_sharpe(returns_input: str, risk_free: float = 0.0) -> float: 
    """CALCULATES Sharpe Ratio. [ACTION]
    
    [RAG Context]
    A core "Super Tool" for risk-adjusted performance evaluation. It calculates the Sharpe Ratio, representing the excess return per unit of volatility.
    
    How to Use:
    - 'returns_input': JSON string of daily returns.
    - 'risk_free': The annual risk-free rate (e.g., 0.02 for 2%).
    - A higher Sharpe ratio indicates better risk-adjusted performance.
    
    Keywords: sharpe metric, risk adjust, portfolio efficiency, volatility reward.
    """
    return stats_ops.stats_sharpe(returns_input, risk_free)

@mcp.tool()
def stats_sortino(returns_input: str, risk_free: float = 0.0) -> float: 
    """CALCULATES Sortino Ratio. [ACTION]
    
    [RAG Context]
    Sortino Ratio (Downside Risk).
    Returns float.
    """
    return stats_ops.stats_sortino(returns_input, risk_free)

@mcp.tool()
def stats_calmar(returns_input: str) -> float: 
    """CALCULATES Calmar Ratio. [ACTION]
    
    [RAG Context]
    Calmar Ratio (CAGR / Max Drawdown).
    Returns float.
    """
    return stats_ops.stats_calmar(returns_input)

@mcp.tool()
def stats_omega(returns_input: str, risk_free: float = 0.0) -> float: 
    """CALCULATES Omega Ratio. [ACTION]
    
    [RAG Context]
    Omega Ratio (Probability weighted).
    Returns float.
    """
    return stats_ops.stats_omega(returns_input, risk_free)

@mcp.tool()
def stats_win_rate(returns_input: str) -> float: 
    """CALCULATES Win Rate. [ACTION]
    
    [RAG Context]
    Percentage of positive periods.
    Returns float.
    """
    return stats_ops.stats_win_rate(returns_input)

@mcp.tool()
def stats_profit_factor(returns_input: str) -> float: 
    """CALCULATES Profit Factor. [ACTION]
    
    [RAG Context]
    Gross Profit / Gross Loss.
    Returns float.
    """
    return stats_ops.stats_profit_factor(returns_input)

@mcp.tool()
def stats_avg_return(returns_input: str) -> float: 
    """CALCULATES Avg Return. [ACTION]
    
    [RAG Context]
    Average daily return.
    Returns float.
    """
    return stats_ops.stats_avg_return(returns_input)

@mcp.tool()
def stats_avg_win(returns_input: str) -> float: 
    """CALCULATES Avg Win. [ACTION]
    
    [RAG Context]
    Average return of winning periods.
    Returns float.
    """
    return stats_ops.stats_avg_win(returns_input)

@mcp.tool()
def stats_avg_loss(returns_input: str) -> float: 
    """CALCULATES Avg Loss. [ACTION]
    
    [RAG Context]
    Average return of losing periods.
    Returns float.
    """
    return stats_ops.stats_avg_loss(returns_input)

@mcp.tool()
def stats_comp(returns_input: str) -> float: 
    """CALCULATES Compounding Return. [ACTION]
    
    [RAG Context]
    Compounded returns.
    Returns float.
    """
    return stats_ops.stats_comp(returns_input)

@mcp.tool()
def stats_kelly_criterion(returns_input: str) -> float: 
    """CALCULATES Kelly Criterion. [ACTION]
    
    [RAG Context]
    Optimal leverage size.
    Returns float.
    """
    return stats_ops.stats_kelly_criterion(returns_input)

@mcp.tool()
def stats_payoff_ratio(returns_input: str) -> float: 
    """CALCULATES Payoff Ratio. [ACTION]
    
    [RAG Context]
    Avg Win / Avg Loss.
    Returns float.
    """
    return stats_ops.stats_payoff_ratio(returns_input)

@mcp.tool()
def stats_common_sense_ratio(returns_input: str) -> float: 
    """CALCULATES Common Sense Ratio. [ACTION]
    
    [RAG Context]
    Common Sense Ratio (Tail Ratio * Gain/Loss).
    Returns float.
    """
    return stats_ops.stats_common_sense_ratio(returns_input)

@mcp.tool()
def stats_expectancy(returns_input: str) -> float: 
    """CALCULATES Expectancy. [ACTION]
    
    [RAG Context]
    Expected return per trade.
    Returns float.
    """
    return stats_ops.stats_expectancy(returns_input)

# ==========================================
# 3. Risk
# ==========================================
@mcp.tool()
def risk_max_drawdown(returns_input: str) -> float: 
    """CALCULATES Max Drawdown. [ACTION]
    
    [RAG Context]
    A critical "Super Tool" for risk assessment. It identifies the "worst-case scenario" by calculating the maximum peak-to-trough decline in a portfolio's equity curve.
    
    How to Use:
    - Input the daily returns data.
    - Essential for understanding the historical depth of losses a strategy has endured.
    
    Keywords: peak to trough, worst loss, drawdown depth, risk tolerance.
    """
    return risk_ops.risk_max_drawdown(returns_input)

@mcp.tool()
def risk_avg_drawdown(returns_input: str) -> float: 
    """CALCULATES Avg Drawdown. [ACTION]
    
    [RAG Context]
    Average depth of drawdowns.
    Returns float.
    """
    return risk_ops.risk_avg_drawdown(returns_input)

@mcp.tool()
def risk_volatility(returns_input: str) -> float: 
    """CALCULATES Volatility. [ACTION]
    
    [RAG Context]
    Standard deviation of returns.
    Returns float.
    """
    return risk_ops.risk_volatility(returns_input)

@mcp.tool()
def risk_var(returns_input: str, sigma: float = 1.0) -> float: 
    """CALCULATES VaR. [ACTION]
    
    [RAG Context]
    Value at Risk (VaR).
    Returns float.
    """
    return risk_ops.risk_var(returns_input, sigma)

@mcp.tool()
def risk_cvar(returns_input: str, sigma: float = 1.0) -> float: 
    """CALCULATES CVaR. [ACTION]
    
    [RAG Context]
    Conditional Value at Risk (Expected Shortfall).
    Returns float.
    """
    return risk_ops.risk_cvar(returns_input, sigma)

@mcp.tool()
def risk_skew(returns_input: str) -> float: 
    """CALCULATES Skew. [ACTION]
    
    [RAG Context]
    Skewness of return distribution.
    Returns float.
    """
    return risk_ops.risk_skew(returns_input)

@mcp.tool()
def risk_kurtosis(returns_input: str) -> float: 
    """CALCULATES Kurtosis. [ACTION]
    
    [RAG Context]
    Kurtosis of return distribution.
    Returns float.
    """
    return risk_ops.risk_kurtosis(returns_input)

@mcp.tool()
def risk_ulcer_index(returns_input: str) -> float: 
    """CALCULATES Ulcer Index. [ACTION]
    
    [RAG Context]
    Measures downside risk (depth & duration).
    Returns float.
    """
    return risk_ops.risk_ulcer_index(returns_input)

@mcp.tool()
def risk_serenity_index(returns_input: str, risk_free: float = 0.0) -> float: 
    """CALCULATES Serenity Index. [ACTION]
    
    [RAG Context]
    Risk-adjusted return metric.
    Returns float.
    """
    return risk_ops.risk_serenity_index(returns_input, risk_free)

@mcp.tool()
def risk_tail_ratio(returns_input: str) -> float: 
    """CALCULATES Tail Ratio. [ACTION]
    
    [RAG Context]
    Ratio of 95th percentile to 5th percentile.
    Returns float.
    """
    return risk_ops.risk_tail_ratio(returns_input)

@mcp.tool()
def risk_risk_return_ratio(returns_input: str) -> float: 
    """CALCULATES Risk-Return Ratio. [ACTION]
    
    [RAG Context]
    Avg Return / Volatility.
    Returns float.
    """
    return risk_ops.risk_risk_return_ratio(returns_input)

# ==========================================
# 4. Comparative
# ==========================================
# ==========================================
# 4. Comparative
# ==========================================
@mcp.tool()
def compare_alpha(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float: 
    """CALCULATES Alpha. [ACTION]
    
    [RAG Context]
    Excess return vs benchmark.
    Returns float.
    """
    return compare_ops.compare_alpha(returns_input, benchmark_input, risk_free)

@mcp.tool()
def compare_beta(returns_input: str, benchmark_input: str = "SPY") -> float: 
    """CALCULATES Beta. [ACTION]
    
    [RAG Context]
    Sensitivity to benchmark movements.
    Returns float.
    """
    return compare_ops.compare_beta(returns_input, benchmark_input)

@mcp.tool()
def compare_r_squared(returns_input: str, benchmark_input: str = "SPY") -> float: 
    """CALCULATES R-Squared. [ACTION]
    
    [RAG Context]
    Correlation with benchmark squared.
    Returns float.
    """
    return compare_ops.compare_r_squared(returns_input, benchmark_input)

@mcp.tool()
def compare_correlation(returns_input: str, benchmark_input: str = "SPY") -> float: 
    """CALCULATES Correlation. [ACTION]
    
    [RAG Context]
    Correlation with benchmark.
    Returns float.
    """
    return compare_ops.compare_correlation(returns_input, benchmark_input)

@mcp.tool()
def compare_information_ratio(returns_input: str, benchmark_input: str = "SPY") -> float: 
    """CALCULATES Information Ratio. [ACTION]
    
    [RAG Context]
    Active Return / Tracking Error.
    Returns float.
    """
    return compare_ops.compare_information_ratio(returns_input, benchmark_input)

@mcp.tool()
def compare_treynor_ratio(returns_input: str, benchmark_input: str = "SPY", risk_free: float = 0.0) -> float: 
    """CALCULATES Treynor Ratio. [ACTION]
    
    [RAG Context]
    Excess Return / Beta.
    Returns float.
    """
    return compare_ops.compare_treynor_ratio(returns_input, benchmark_input, risk_free)

# ==========================================
# 5. Plotting
# ==========================================
# ==========================================
# 5. Plotting
# ==========================================
@mcp.tool()
def plot_snapshot(returns_input: str, title: str = "Performance Snapshot") -> str: 
    """PLOTS performance snapshot. [ACTION]
    
    [RAG Context]
    Generates a summary dashboard plot.
    Returns base64 image string.
    """
    return plot_ops.plot_snapshot(returns_input, title)

@mcp.tool()
def plot_cumulative_returns(returns_input: str, benchmark_input: str = None) -> str: 
    """PLOTS cumulative returns. [ACTION]
    
    [RAG Context]
    Plots cumulative returns vs benchmark.
    Returns base64 image string.
    """
    return plot_ops.plot_cumulative_returns(returns_input, benchmark_input)

@mcp.tool()
def plot_drawdown(returns_input: str) -> str: 
    """PLOTS drawdown. [ACTION]
    
    [RAG Context]
    Plots underwater curve (drawdowns).
    Returns base64 image string.
    """
    return plot_ops.plot_drawdown(returns_input)

@mcp.tool()
def plot_daily_returns(returns_input: str) -> str: 
    """PLOTS daily returns. [ACTION]
    
    [RAG Context]
    Plots daily returns histogram/bar.
    Returns base64 image string.
    """
    return plot_ops.plot_daily_returns(returns_input)

@mcp.tool()
def plot_monthly_heatmap(returns_input: str) -> str: 
    """PLOTS monthly heatmap. [ACTION]
    
    [RAG Context]
    Plots monthly returns heatmap.
    Returns base64 image string.
    """
    return plot_ops.plot_monthly_heatmap(returns_input)

@mcp.tool()
def plot_distribution(returns_input: str) -> str: 
    """PLOTS return distribution. [ACTION]
    
    [RAG Context]
    Plots distribution of returns.
    Returns base64 image string.
    """
    return plot_ops.plot_distribution(returns_input)

@mcp.tool()
def plot_rolling_sharpe(returns_input: str, periods: int = 126) -> str: 
    """PLOTS rolling Sharpe. [ACTION]
    
    [RAG Context]
    Plots rolling Sharpe ratio.
    Returns base64 image string.
    """
    return plot_ops.plot_rolling_sharpe(returns_input, periods)

@mcp.tool()
def plot_rolling_volatility(returns_input: str, periods: int = 126) -> str: 
    """PLOTS rolling volatility. [ACTION]
    
    [RAG Context]
    Plots rolling volatility.
    Returns base64 image string.
    """
    return plot_ops.plot_rolling_volatility(returns_input, periods)

@mcp.tool()
def plot_rolling_beta(returns_input: str, benchmark_input: str = "SPY", periods: int = 126) -> str: 
    """PLOTS rolling Beta. [ACTION]
    
    [RAG Context]
    Plots rolling Beta to benchmark.
    Returns base64 image string.
    """
    return plot_ops.plot_rolling_beta(returns_input, benchmark_input, periods)

# ==========================================
# 6. Reports
# ==========================================
@mcp.tool()
def report_html(returns_input: str, benchmark_input: str = None, title: str = "Strategy Report") -> str: 
    """GENERATES HTML report. [ACTION]
    
    [RAG Context]
    Creates full HTML teardown report.
    Returns HTML string.
    """
    return report_ops.report_html(returns_input, benchmark_input, title)

@mcp.tool()
def report_metrics(returns_input: str, benchmark_input: str = None) -> str: 
    """GENERATES metrics report. [ACTION]
    
    [RAG Context]
    Returns key metrics table.
    Returns JSON string.
    """
    return report_ops.report_metrics(returns_input, benchmark_input)

@mcp.tool()
def report_full(returns_input: str) -> str: 
    """GENERATES full report. [ACTION]
    
    [RAG Context]
    Comprehensive performance report.
    Returns JSON string.
    """
    return report_ops.report_full(returns_input)

# ==========================================
# 7. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_get_stats(tickers: List[str], period: str = "max") -> Dict[str, Dict[str, float]]: 
    """FETCHES bulk stats. [ACTION]
    
    [RAG Context]
    Get key stats for multiple tickers.
    Returns JSON dict.
    """
    return bulk_ops.bulk_get_stats(tickers, period)

@mcp.tool()
def bulk_compare_tickers(tickers: List[str], benchmark: str = "SPY", period: str = "max") -> Dict[str, Dict[str, float]]: 
    """COMPARES bulk tickers. [ACTION]
    
    [RAG Context]
    Compare multiple tickers vs benchmark.
    Returns JSON dict.
    """
    return bulk_ops.bulk_compare_tickers(tickers, benchmark, period)

@mcp.tool()
def super_tearsheet(returns_input: str, benchmark_input: str = "SPY", title: str = "Analysis") -> Dict[str, Any]: 
    """GENERATES Super Tearsheet. [ACTION]
    
    [RAG Context]
    The ultimate "Super Tool" for portfolio audits. It combines statistical metrics, risk analysis, and comprehensive visualizations into a single high-level data structure.
    
    How to Use:
    - Compares your 'returns_input' against a 'benchmark_input' (e.g., S&P 500).
    - Returns a dictionary containing key metrics (Alpha, Beta, Sharpe) and multiple base64-encoded plots (Cumulative Returns, Drawdown heatmap).
    
    Keywords: performance audit, full tearsheet, strategy deepdive, visual report.
    """
    return super_ops.super_tearsheet(returns_input, benchmark_input, title)

@mcp.tool()
def diagnose_strategy(returns_input: str) -> Dict[str, Any]: 
    """DIAGNOSES strategy. [ACTION]
    
    [RAG Context]
    Identify strategy weaknesses.
    Returns JSON dict.
    """
    return super_ops.diagnose_strategy(returns_input)

@mcp.tool()
def rolling_stats_dataframe(returns_input: str, window: int = 126) -> str: 
    """CALCULATES rolling stats. [ACTION]
    
    [RAG Context]
    Get rolling stats dataframe (Sharpe, Vol, etc).
    Returns JSON string.
    """
    return super_ops.rolling_stats_dataframe(returns_input, window)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class QuantstatsServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

