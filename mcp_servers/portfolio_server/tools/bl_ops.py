from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import black_litterman, risk_models
from pypfopt.black_litterman import BlackLittermanModel
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def bl_market_implied_risk_aversion(prices_input: str, risk_free_rate: float = 0.02) -> float:
    """Calculate market-implied risk aversion (delta)."""
    # Requires market prices ideally, but often estimated from the portfolio itself if it's broad
    # For correctness, use S&P500 as market cap weights usually? 
    # BL requires market_prices to compute returns.
    # PyPortfolioOpt separates this.
    # We will assume equal weights or provide market caps if available?
    # Simplification: use market_implied_risk_aversion with raw prices
    df = _parse_prices(prices_input)
    # This function usually takes market prices separately. If user passes broad index df...
    # Let's assume input IS market prices for this call
    market_prices = df.iloc[:, 0] # Use first col as market proxy?
    # Actually, pypfopt expects `market_prices` (Series)
    # The user might just want delta from SPY
    delta = black_litterman.market_implied_risk_aversion(market_prices, risk_free_rate=risk_free_rate)
    return float(delta)

def bl_compute_posterior(prices_input: str, absolute_views: Dict[str, float], risk_aversion: float = 1.0) -> Dict[str, Any]:
    """
    Compute Black-Litterman posterior returns and covariance.
    
    :param prices_input: Asset prices
    :param absolute_views: Dict of {ticker: expected_return} e.g. {"AAPL": 0.20}
    :param risk_aversion: Delta (defaults to 1, or use calculated market delta)
    """
    df = _parse_prices(prices_input)
    S = risk_models.sample_cov(df)
    
    # Prior: We used to need market caps, but we can default to equal weights or None
    # If no market caps, we assume the input prices REPRESENTS the market equilibrium (roughly)
    # Detailed BL is complex. 
    # Let's simple implementation: use Equal Weights as "Market" to get Prior? 
    # Or cleaner: Assume equilibrium returns = mean historical? 
    # No, BL uses Implied Returns.
    
    # We will compute market implied prior returns assuming equal weights for simplicity if no caps provided
    # (In real app, we need caps tool).
    mcaps = {ticker: 1.0 for ticker in df.columns} # Equal caps
    
    delta = risk_aversion
    # Prior
    prior_returns = black_litterman.market_implied_prior_returns(mcaps, delta, S)
    
    bl = BlackLittermanModel(S, pi=prior_returns, absolute_views=absolute_views)
    ret_bl = bl.bl_returns()
    cov_bl = bl.bl_cov()
    
    return {
        "posterior_returns": ret_bl.to_dict(),
        "posterior_covariance": cov_bl.to_json(orient='split') # DataFrame json
    }

def bl_weights(prices_input: str, absolute_views: Dict[str, float]) -> Dict[str, float]:
    """Get optimized weights using BL posterior returns (Max Sharpe)."""
    # Wrapper that does BL then Max Sharpe
    res = bl_compute_posterior(prices_input, absolute_views)
    mu_bl = pd.Series(res['posterior_returns'])
    S_bl = pd.read_json(res['posterior_covariance'], orient='split')
    
    from pypfopt import EfficientFrontier
    ef = EfficientFrontier(mu_bl, S_bl)
    ef.max_sharpe()
    return ef.clean_weights()
