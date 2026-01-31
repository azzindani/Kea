# /// script
# dependencies = [
#   "mcp",
# ]
# ///


from __future__ import annotations
import asyncio
from mcp.server.fastmcp import FastMCP

# Phase 1: Core & Bulk
from mcp_servers.mibian_server.tools.bulk import price_option_chain, calculate_iv_surface

# Phase 2: Pricing
from mcp_servers.mibian_server.tools.pricing import calculate_bs_price, calculate_gk_price, calculate_me_price

# Phase 3: Greeks
from mcp_servers.mibian_server.tools.greeks import (
    calculate_bs_delta, calculate_bs_gamma, calculate_bs_theta, calculate_bs_vega, calculate_bs_rho,
    calculate_gk_delta, calculate_gk_theta
)

# Phase 4: Volatility
from mcp_servers.mibian_server.tools.volatility import calculate_implied_volatility
# Phase 2 (Expansion)
from mcp_servers.mibian_server.tools.utilities import (
    calculate_put_call_parity, calculate_moneyness, calculate_probability_itm, calculate_dual_delta
)
from mcp_servers.mibian_server.tools.simulation import simulate_greek_scenario
# Phase 3
from mcp_servers.mibian_server.tools.strategies import calculate_strategy_price
from mcp_servers.mibian_server.tools.advanced_greeks import (
    calculate_advanced_greeks, calculate_vanna, calculate_vomma, calculate_charm, calculate_speed
)
from mcp_servers.mibian_server.tools.exotics import calculate_binary_price
# Phase 4
from mcp_servers.mibian_server.tools.american import calculate_american_price
from mcp_servers.mibian_server.tools.barriers import calculate_barrier_price

mcp = FastMCP("mibian_server")

# 1. Bulk (High Value)
mcp.add_tool(price_option_chain)
mcp.add_tool(calculate_iv_surface)

# 2. Pricing (10 Tools)
mcp.add_tool(calculate_bs_price)
# Aliases
mcp.add_tool(calculate_bs_price, name="get_bs_call_price")
mcp.add_tool(calculate_bs_price, name="get_bs_put_price")

mcp.add_tool(calculate_gk_price)
mcp.add_tool(calculate_gk_price, name="get_gk_call_price")
mcp.add_tool(calculate_gk_price, name="get_gk_put_price")

mcp.add_tool(calculate_me_price)
mcp.add_tool(calculate_me_price, name="get_me_call_price")
mcp.add_tool(calculate_me_price, name="get_me_put_price")

# 3. Greeks - BS (12 Tools)
mcp.add_tool(calculate_bs_delta)
mcp.add_tool(calculate_bs_delta, name="get_bs_call_delta")
mcp.add_tool(calculate_bs_delta, name="get_bs_put_delta")

mcp.add_tool(calculate_bs_gamma)
# Gamma is same for Call/Put

mcp.add_tool(calculate_bs_theta)
mcp.add_tool(calculate_bs_theta, name="get_bs_call_theta")
mcp.add_tool(calculate_bs_theta, name="get_bs_put_theta")

mcp.add_tool(calculate_bs_vega)

mcp.add_tool(calculate_bs_rho)
mcp.add_tool(calculate_bs_rho, name="get_bs_call_rho")
mcp.add_tool(calculate_bs_rho, name="get_bs_put_rho")

# 4. Greeks - GK (12 Tools)
mcp.add_tool(calculate_gk_delta)
mcp.add_tool(calculate_gk_delta, name="get_gk_call_delta")
mcp.add_tool(calculate_gk_delta, name="get_gk_put_delta")

mcp.add_tool(calculate_gk_theta)
mcp.add_tool(calculate_gk_theta, name="get_gk_call_theta")
mcp.add_tool(calculate_gk_theta, name="get_gk_put_theta")

# 5. Volatility
mcp.add_tool(calculate_implied_volatility)
mcp.add_tool(calculate_implied_volatility, name="get_bs_iv")

# 6. Analysis & Probability (Phase 2)
mcp.add_tool(calculate_put_call_parity)
mcp.add_tool(calculate_moneyness)
mcp.add_tool(calculate_probability_itm)
mcp.add_tool(calculate_dual_delta)

# 7. Simulation (Phase 2)
mcp.add_tool(simulate_greek_scenario)

# 8. Strategy & Advanced Greeks (Phase 3)
mcp.add_tool(calculate_strategy_price)

mcp.add_tool(calculate_advanced_greeks)
mcp.add_tool(calculate_vanna)
mcp.add_tool(calculate_vomma)
mcp.add_tool(calculate_charm)
mcp.add_tool(calculate_speed)

mcp.add_tool(calculate_binary_price)

# 9. Structural (Phase 4)
mcp.add_tool(calculate_american_price)
mcp.add_tool(calculate_barrier_price)

if __name__ == "__main__":
    mcp.run()

