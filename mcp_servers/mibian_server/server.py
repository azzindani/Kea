from __future__ import annotations

import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "numpy",
#   "scipy",
# ]
# ///
import asyncio
from mcp.server.fastmcp import FastMCP

# Phase 1: Core & Bulk
from tools import bulk

# Phase 2: Pricing
from tools import pricing

# Phase 3: Greeks
from tools import greeks

# Phase 4: Volatility
from tools import volatility

# Phase 2 (Expansion)
from tools import utilities
from tools import simulation

# Phase 3
from tools import strategies
from tools import advanced_greeks
from tools import exotics

# Phase 4
from tools import american
from tools import barriers

from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("mibian_server")

# ==========================================
# 1. Bulk (High Value)
# ==========================================

@mcp.tool()
async def price_option_chain(data: list[dict]) -> str:
    """PRICES option chain (Bulk). [ACTION]
    
    [RAG Context]
    Calculates prices and Greeks for a list of options.
    Args:
        data: List of dicts with keys: underlying, strike, interest, days, volatility.
    """
    return await bulk.price_option_chain(data)

@mcp.tool()
async def calculate_iv_surface(data: list[dict]) -> str:
    """CALCULATES Implied Volatility Surface (Bulk). [ACTION]
    
    [RAG Context]
    Calculates IV for a list of options given market prices.
    Args:
        data: List of dicts with keys: underlying, strike, interest, days, call_price OR put_price.
    """
    return await bulk.calculate_iv_surface(data)


# ==========================================
# 2. Pricing
# ==========================================

@mcp.tool()
async def calculate_bs_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Black-Scholes Price. [ACTION]
    
    [RAG Context]
    Standard European Option Price (Call & Put).
    """
    return await pricing.calculate_bs_price(underlying, strike, interest, days, volatility)

# Aliases
@mcp.tool(name="get_bs_call_price")
async def get_bs_call_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Call Price. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Call Price.
    """
    return await pricing.calculate_bs_price(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_put_price")
async def get_bs_put_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Put Price. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Put Price.
    """
    return await pricing.calculate_bs_price(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_gk_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Garman-Kohlhagen Price. [ACTION]
    
    [RAG Context]
    Currency Option Price (Foreign Exchange).
    """
    return await pricing.calculate_gk_price(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_call_price")
async def get_gk_call_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Call Price. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Call Price.
    """
    return await pricing.calculate_gk_price(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_put_price")
async def get_gk_put_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Put Price. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Put Price.
    """
    return await pricing.calculate_gk_price(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_me_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Merton Price. [ACTION]
    
    [RAG Context]
    Option on stock with continuous dividends (Merton Model).
    """
    return await pricing.calculate_me_price(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_me_call_price")
async def get_me_call_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES Merton Call Price. [ACTION]
    
    [RAG Context]
    Shortcut for Merton Call Price.
    """
    return await pricing.calculate_me_price(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_me_put_price")
async def get_me_put_price(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES Merton Put Price. [ACTION]
    
    [RAG Context]
    Shortcut for Merton Put Price.
    """
    return await pricing.calculate_me_price(underlying, strike, interest, days, volatility)


# ==========================================
# 3. Greeks - BS
# ==========================================

@mcp.tool()
async def calculate_bs_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Delta. [ACTION]
    
    [RAG Context]
    Rate of change of option price with respect to underlying price.
    """
    return await greeks.calculate_bs_delta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_call_delta")
async def get_bs_call_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Call Delta. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Call Delta.
    """
    return await greeks.calculate_bs_delta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_put_delta")
async def get_bs_put_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Put Delta. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Put Delta.
    """
    return await greeks.calculate_bs_delta(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_bs_gamma(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Gamma. [ACTION]
    
    [RAG Context]
    Rate of change of Delta with respect to underlying price.
    Same for Call and Put.
    """
    return await greeks.calculate_bs_gamma(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_bs_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Theta. [ACTION]
    
    [RAG Context]
    Rate of change of option price with respect to time (Time Decay).
    """
    return await greeks.calculate_bs_theta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_call_theta")
async def get_bs_call_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Call Theta. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Call Theta.
    """
    return await greeks.calculate_bs_theta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_put_theta")
async def get_bs_put_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Put Theta. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Put Theta.
    """
    return await greeks.calculate_bs_theta(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_bs_vega(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Vega. [ACTION]
    
    [RAG Context]
    Rate of change of option price with respect to volatility.
    Same for Call and Put.
    """
    return await greeks.calculate_bs_vega(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_bs_rho(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES BS Rho. [ACTION]
    
    [RAG Context]
    Rate of change of option price with respect to interest rate.
    """
    return await greeks.calculate_bs_rho(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_call_rho")
async def get_bs_call_rho(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Call Rho. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Call Rho.
    """
    return await greeks.calculate_bs_rho(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_bs_put_rho")
async def get_bs_put_rho(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES BS Put Rho. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Put Rho.
    """
    return await greeks.calculate_bs_rho(underlying, strike, interest, days, volatility)


# ==========================================
# 4. Greeks - GK
# ==========================================

@mcp.tool()
async def calculate_gk_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES GK Delta. [ACTION]
    
    [RAG Context]
    Garman-Kohlhagen Delta (Currencies).
    """
    return await greeks.calculate_gk_delta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_call_delta")
async def get_gk_call_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Call Delta. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Call Delta.
    """
    return await greeks.calculate_gk_delta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_put_delta")
async def get_gk_put_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Put Delta. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Put Delta.
    """
    return await greeks.calculate_gk_delta(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_gk_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES GK Theta. [ACTION]
    
    [RAG Context]
    Garman-Kohlhagen Theta (Currencies).
    """
    return await greeks.calculate_gk_theta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_call_theta")
async def get_gk_call_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Call Theta. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Call Theta.
    """
    return await greeks.calculate_gk_theta(underlying, strike, interest, days, volatility)

@mcp.tool(name="get_gk_put_theta")
async def get_gk_put_theta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """FETCHES GK Put Theta. [ACTION]
    
    [RAG Context]
    Shortcut for Garman-Kohlhagen Put Theta.
    """
    return await greeks.calculate_gk_theta(underlying, strike, interest, days, volatility)


# ==========================================
# 5. Volatility
# ==========================================

@mcp.tool()
async def calculate_implied_volatility(underlying: float, strike: float, interest: float, days: float, call_price: float = None, put_price: float = None, model: str = "BS") -> str:
    """CALCULATES Implied Volatility. [ACTION]
    
    [RAG Context]
    Iteratively solves for volatility given an option price.
    Args:
        call_price: Market price of call (optional).
        put_price: Market price of put (optional).
    """
    return await volatility.calculate_implied_volatility(underlying, strike, interest, days, call_price, put_price, model)

@mcp.tool(name="get_bs_iv")
async def get_bs_iv(underlying: float, strike: float, interest: float, days: float, call_price: float = None, put_price: float = None) -> str:
    """FETCHES BS Implied Volatility. [ACTION]
    
    [RAG Context]
    Shortcut for Black-Scholes Implied Volatility.
    """
    return await volatility.calculate_implied_volatility(underlying, strike, interest, days, call_price, put_price, "BS")


# ==========================================
# 6. Analysis & Probability
# ==========================================

@mcp.tool()
async def calculate_put_call_parity(call_price: float, put_price: float, underlying: float, strike: float, interest: float, days: float) -> str:
    """CHECKS Put-Call Parity. [ACTION]
    
    [RAG Context]
    Identifies arbitrage opportunities by checking if Call + PV(K) = Put + S.
    Returns deviation amount.
    """
    return await utilities.calculate_put_call_parity(call_price, put_price, underlying, strike, interest, days)

@mcp.tool()
async def calculate_moneyness(underlying: float, strike: float) -> str:
    """CALCULATES Moneyness. [ACTION]
    
    [RAG Context]
    Returns S/K ratio and log moneyness.
    """
    return await utilities.calculate_moneyness(underlying, strike)

@mcp.tool()
async def calculate_probability_itm(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Probability of Expiring ITM. [ACTION]
    
    [RAG Context]
    Estimates probability that option expires in-the-money (N(d2)).
    """
    return await utilities.calculate_probability_itm(underlying, strike, interest, days, volatility)

@mcp.tool()
async def calculate_dual_delta(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Dual Delta. [ACTION]
    
    [RAG Context]
    Probability of expiring ITM (Alias).
    """
    return await utilities.calculate_dual_delta(underlying, strike, interest, days, volatility)


# ==========================================
# 7. Simulation
# ==========================================

@mcp.tool()
async def simulate_greek_scenario(underlying_start: float, underlying_end: float, steps: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """SIMULATES Greek Scenario. [ACTION]
    
    [RAG Context]
    Simulates price and Greeks across a range of underlying prices.
    Returns JSON dataset for plotting.
    """
    return await simulation.simulate_greek_scenario(underlying_start, underlying_end, steps, strike, interest, days, volatility)


# ==========================================
# 8. Strategy & Advanced Greeks
# ==========================================

@mcp.tool()
async def calculate_strategy_price(legs: list[dict]) -> str:
    """CALCULATES Strategy Price (Multi-Leg). [ACTION]
    
    [RAG Context]
    Pricing and Greeks for complex strategies (e.g., Iron Condor, Straddle).
    Args:
        legs: List of dicts specifying each option leg.
    """
    return await strategies.calculate_strategy_price(legs)

@mcp.tool()
async def calculate_advanced_greeks(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Advanced Greeks. [ACTION]
    
    [RAG Context]
    Computes higher-order Greeks: Vanna, Vomma, Charm, Speed, Zomma.
    """
    return await advanced_greeks.calculate_advanced_greeks(underlying, strike, interest, days, volatility)

@mcp.tool()
async def calculate_vanna(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Vanna. [ACTION]
    
    [RAG Context]
    Sensitivity of Delta to Volatility (dDelta/dVol).
    """
    return await advanced_greeks.calculate_vanna(underlying, strike, interest, days, volatility)

@mcp.tool()
async def calculate_vomma(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Vomma. [ACTION]
    
    [RAG Context]
    Sensitivity of Vega to Volatility (dVega/dVol).
    """
    return await advanced_greeks.calculate_vomma(underlying, strike, interest, days, volatility)

@mcp.tool()
async def calculate_charm(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Charm. [ACTION]
    
    [RAG Context]
    Sensitivity of Delta to Time (dDelta/dTime).
    """
    return await advanced_greeks.calculate_charm(underlying, strike, interest, days, volatility)

@mcp.tool()
async def calculate_speed(underlying: float, strike: float, interest: float, days: float, volatility: float) -> str:
    """CALCULATES Speed. [ACTION]
    
    [RAG Context]
    Sensitivity of Gamma to Underlying Price (dGamma/dS).
    """
    return await advanced_greeks.calculate_speed(underlying, strike, interest, days, volatility)


@mcp.tool()
async def calculate_binary_price(underlying: float, strike: float, interest: float, days: float, volatility: float, payout: float = 100.0) -> str:
    """CALCULATES Binary Option Price. [ACTION]
    
    [RAG Context]
    Cash-or-Nothing Option Price.
    Args:
        payout: Cash amount paid if ITM.
    """
    return await exotics.calculate_binary_price(underlying, strike, interest, days, volatility, payout)


# ==========================================
# 9. Structural
# ==========================================

@mcp.tool()
async def calculate_american_price(underlying: float, strike: float, interest: float, days: float, volatility: float, dividend_yield: float = 0.0) -> str:
    """CALCULATES American Option Price. [ACTION]
    
    [RAG Context]
    Uses Barone-Adesi-Whaley approximation for American style options.
    """
    return await american.calculate_american_price(underlying, strike, interest, days, volatility, dividend_yield)

@mcp.tool()
async def calculate_barrier_price(underlying: float, strike: float, barrier: float, interest: float, days: float, volatility: float, barrier_type: str = 'down-and-out', option_type: str = 'call', rebate: float = 0.0) -> str:
    """CALCULATES Barrier Option Price. [ACTION]
    
    [RAG Context]
    Uses Reiner-Rubinstein formula for barrier options.
    Args:
        barrier_type: 'down-and-out', 'down-and-in', etc.
        rebate: Amount paid if barrier hit (for knock-out).
    """
    return await barriers.calculate_barrier_price(underlying, strike, barrier, interest, days, volatility, barrier_type, option_type, rebate)


if __name__ == "__main__":
    mcp.run()
