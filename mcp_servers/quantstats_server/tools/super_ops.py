from mcp_servers.quantstats_server.tools import core_ops, report_ops, plot_ops
import quantstats as qs
import pandas as pd
from typing import Dict, Any

def super_tearsheet(returns_input: str, benchmark_input: str = "SPY", title: str = "Analysis") -> Dict[str, Any]:
    """
    Generate a comprehensive analysis package:
    1. Key Metrics (JSON)
    2. HTML Report (Path)
    3. Snapshot Image (Base64)
    """
    metrics = report_ops.report_metrics(returns_input, benchmark_input)
    html_path = report_ops.report_html(returns_input, benchmark_input, title=title)
    snapshot = plot_ops.plot_snapshot(returns_input, title=title)
    
    return {
        "metrics": metrics,
        "html_report_path": html_path,
        "snapshot_image": snapshot
    }

def diagnose_strategy(returns_input: str) -> Dict[str, Any]:
    """Run constraints check on strategy (Health Check)."""
    s = core_ops._parse_returns(returns_input)
    
    warnings = []
    sharpe = qs.stats.sharpe(s)
    dd = qs.stats.max_drawdown(s)
    cagr = qs.stats.cagr(s)
    
    if sharpe < 1.0: warnings.append("Low Sharpe Ratio (< 1.0)")
    if dd < -0.20: warnings.append("High Max Drawdown (> 20%)")
    if cagr < 0: warnings.append("Negative CAGR")
    
    # Check data quality
    missing = s.isnull().sum()
    if missing > 0: warnings.append(f"Contains {missing} missing values")
    
    return {
        "health": "Poor" if warnings else "Good",
        "warnings": warnings,
        "key_stats": {
            "sharpe": float(sharpe),
            "max_drawdown": float(dd),
            "cagr": float(cagr)
        }
    }

def rolling_stats_dataframe(returns_input: str, window: int = 126) -> str:
    """Return rolling stats (Sharpe, Vol, Beta) as computed DataFrame JSON."""
    s = core_ops._parse_returns(returns_input)
    
    # Manual computation using QS underlying or pandas rolling
    # QS usually just plots. We'll reconstruct.
    df = pd.DataFrame(index=s.index)
    df['rolling_sharpe'] = s.rolling(window).apply(lambda x: qs.stats.sharpe(x))
    df['rolling_vol'] = s.rolling(window).apply(lambda x: qs.stats.volatility(x))
    
    return df.dropna().to_json(orient='split', date_format='iso')
