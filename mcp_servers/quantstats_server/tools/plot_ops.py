from mcp_servers.quantstats_server.tools.core_ops import _parse_returns
import quantstats as qs
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

def _fig_to_b64() -> str:
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def plot_snapshot(returns_input: str, title: str = "Performance Snapshot") -> str:
    """Generate summary snapshot plot."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.snapshot(s, title=title, show=False)
    return _fig_to_b64()

def plot_cumulative_returns(returns_input: str, benchmark_input: str = None) -> str:
    """Plot cumulative returns."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    b = None
    if benchmark_input:
        b = _parse_returns(benchmark_input) if len(benchmark_input) > 20 else qs.utils.download_returns(benchmark_input)
        if b is not None and not isinstance(b.index, pd.DatetimeIndex):
            b.index = pd.to_datetime(b.index)
    qs.plots.returns(s, benchmark=b, show=False)
    return _fig_to_b64()

def plot_drawdown(returns_input: str) -> str:
    """Plot underwater drawdown chart."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.drawdown(s, show=False)
    return _fig_to_b64()

def plot_daily_returns(returns_input: str) -> str:
    """Plot bar chart of daily returns."""
    s = _parse_returns(returns_input)
    # Ensure DatetimeIndex for plotting
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    # daily_returns requires benchmark in some versions
    qs.plots.daily_returns(s, benchmark=None, show=False)
    return _fig_to_b64()

def plot_monthly_heatmap(returns_input: str) -> str:
    """Plot monthly returns heatmap."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.monthly_heatmap(s, show=False)
    return _fig_to_b64()

def plot_distribution(returns_input: str) -> str:
    """Plot histogram of returns."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.histogram(s, show=False)
    return _fig_to_b64()

def plot_rolling_sharpe(returns_input: str, periods: int = 126) -> str:
    """Plot rolling Sharpe ratio."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.rolling_sharpe(s, period=periods, show=False)
    return _fig_to_b64()

def plot_rolling_volatility(returns_input: str, periods: int = 126) -> str:
    """Plot rolling Volatility."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    qs.plots.rolling_volatility(s, period=periods, show=False)
    return _fig_to_b64()

def plot_rolling_beta(returns_input: str, benchmark_input: str = "SPY", periods: int = 126) -> str:
    """Plot rolling Beta."""
    s = _parse_returns(returns_input)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    b = _parse_returns(benchmark_input) if len(benchmark_input) > 20 else qs.utils.download_returns(benchmark_input)
    if b is not None and not isinstance(b.index, pd.DatetimeIndex):
        b.index = pd.to_datetime(b.index)
    qs.plots.rolling_beta(s, benchmark=b, window1=periods, show=False)
    return _fig_to_b64()
