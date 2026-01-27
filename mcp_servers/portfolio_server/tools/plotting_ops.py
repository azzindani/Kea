from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import plotting
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, Any, Optional

def _fig_to_b64() -> str:
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def plot_covariance(risk_matrix_input: str, plot_correlation: bool = False) -> str:
    """Plot covariance matrix heatmap."""
    try:
        S = pd.read_json(risk_matrix_input, orient='split')
    except:
        import json
        S = pd.DataFrame(json.loads(risk_matrix_input))
        
    plotting.plot_covariance(S, plot_correlation=plot_correlation)
    return _fig_to_b64()

def plot_weights(weights: Dict[str, float]) -> str:
    """Plot asset weights as a bar chart."""
    plotting.plot_weights(weights)
    return _fig_to_b64()

def plot_efficient_frontier(prices_input: str, points: int = 100) -> str:
    """Plot the efficient frontier curve."""
    # Plotting EF requires an EF instance that computed it. 
    # MVO plotting often re-runs optimization for points.
    # PyPortfolioOpt plotting.plot_efficient_frontier takes an EF object.
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    
    df = _parse_prices(prices_input)
    mu = expected_returns.mean_historical_return(df)
    S = risk_models.sample_cov(df)
    ef = EfficientFrontier(mu, S)
    
    plotting.plot_efficient_frontier(ef, points=points)
    return _fig_to_b64()

def plot_dendrogram(prices_input: str) -> str:
    """Plot Hierarchical Risk Parity dendrogram."""
    from pypfopt import HRPOpt
    df = _parse_prices(prices_input)
    rets = df.pct_change().dropna()
    hrp = HRPOpt(rets)
    hrp.optimize()
    
    plotting.plot_dendrogram(hrp)
    return _fig_to_b64()
