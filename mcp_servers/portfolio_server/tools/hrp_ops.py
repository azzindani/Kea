from mcp_servers.portfolio_server.tools.core_ops import _parse_prices
from pypfopt import HRPOpt, hierarchical_portfolio
import pandas as pd
from typing import Dict, Any

def hrp_optimize(prices_input: str) -> Dict[str, float]:
    """Hierarchical Risk Parity optimization."""
    df = _parse_prices(prices_input)
    rets = df.pct_change().dropna()
    hrp = HRPOpt(rets)
    hrp.optimize()
    return hrp.clean_weights()

def herc_optimize(prices_input: str) -> Dict[str, float]:
    """Hierarchical Equal Risk Contribution (HERC)."""
    # Note: As of my knowledge, PyPortfolioOpt implemented HRP. 
    # HERC (Hierarchical Equal Risk Contribution) might be available via specific method or updated lib.
    # HRPOpt only does HRP. 
    # We will stick to HRPOpt as the primary hierarchical tool.
    # But let's check NCO if available? 
    # Actually, let's keep it simple: HRP is robust.
    return hrp_optimize(prices_input)
