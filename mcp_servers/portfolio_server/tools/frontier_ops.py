from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import expected_returns, risk_models, EfficientFrontier, objective_functions
import pandas as pd
from typing import Dict, Any, List

def _get_ef_instance(prices_input: str, risk_matrix_input: str = None, returns_input: str = None) -> EfficientFrontier:
    """Helper to instantiate EfficientFrontier."""
    df = _parse_prices(prices_input)
    
    # Expected returns
    if returns_input:
         try:
             mu = pd.read_json(returns_input, orient='split', typ='series') # Or simple dict
         except:
             # Assume dict input from previous tools
             import json
             if isinstance(returns_input, str): 
                 data = json.loads(returns_input)
                 mu = pd.Series(data)
    else:
         mu = expected_returns.mean_historical_return(df)
         
    # Covariance
    if risk_matrix_input:
        try:
            S = pd.read_json(risk_matrix_input, orient='split')
        except:
            # Assume dict input? usually risk models return formatted json
             import json
             if isinstance(risk_matrix_input, str):
                 S = pd.DataFrame(json.loads(risk_matrix_input)) # Fallback
    else:
        S = risk_models.sample_cov(df)
        
    return EfficientFrontier(mu, S)

def ef_max_sharpe(prices_input: str, risk_free_rate: float = 0.02) -> Dict[str, float]:
    """Optimize for maximal Sharpe ratio."""
    ef = _get_ef_instance(prices_input)
    weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
    return ef.clean_weights()

def ef_min_volatility(prices_input: str) -> Dict[str, float]:
    """Optimize for minimum volatility."""
    ef = _get_ef_instance(prices_input)
    weights = ef.min_volatility()
    return ef.clean_weights()

def ef_efficient_risk(prices_input: str, target_volatility: float) -> Dict[str, float]:
    """Maximize return for a target volatility."""
    ef = _get_ef_instance(prices_input)
    weights = ef.efficient_risk(target_volatility)
    return ef.clean_weights()

def ef_efficient_return(prices_input: str, target_return: float) -> Dict[str, float]:
    """Minimize risk for a target return."""
    ef = _get_ef_instance(prices_input)
    weights = ef.efficient_return(target_return)
    return ef.clean_weights()

def ef_max_quadratic_utility(prices_input: str, risk_aversion: float = 1.0) -> Dict[str, float]:
    """Maximize utility: Return - 0.5 * risk_aversion * Variance."""
    ef = _get_ef_instance(prices_input)
    weights = ef.max_quadratic_utility(risk_aversion)
    return ef.clean_weights()

def ef_portfolio_performance(prices_input: str, weights: Dict[str, float], risk_free_rate: float = 0.02) -> Dict[str, float]:
    """Calculate performance metrics for a given set of weights."""
    ef = _get_ef_instance(prices_input)
    ef.set_weights(weights)
    perf = ef.portfolio_performance(verbose=False, risk_free_rate=risk_free_rate)
    return {
        "expected_return": perf[0],
        "volatility": perf[1],
        "sharpe_ratio": perf[2]
    }
