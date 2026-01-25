
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

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

logger = get_logger(__name__)

class MibianServer(MCPServer):
    """
    Mibian MCP Server.
    Options Pricing & Greeks.
    """
    
    def __init__(self) -> None:
        super().__init__(name="mibian_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Bulk (High Value)
        self.register_tool(name="price_option_chain", description="BULK: Price entire option chain.", handler=price_option_chain, parameters={"data": {"type": "array"}})
        self.register_tool(name="calculate_iv_surface", description="BULK: Calculate IV Surface.", handler=calculate_iv_surface, parameters={"data": {"type": "array"}})
        
        # 2. Pricing (10 Tools)
        self.register_tool(name="calculate_bs_price", description="PRICE: Black-Scholes (All).", handler=calculate_bs_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_call_price", description="PRICE: BS Call Price.", handler=calculate_bs_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_put_price", description="PRICE: BS Put Price.", handler=calculate_bs_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        self.register_tool(name="calculate_gk_price", description="PRICE: Garman-Kohlhagen (All).", handler=calculate_gk_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_call_price", description="PRICE: GK Call Price.", handler=calculate_gk_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_put_price", description="PRICE: GK Put Price.", handler=calculate_gk_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})

        self.register_tool(name="calculate_me_price", description="PRICE: Merton (All).", handler=calculate_me_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_me_call_price", description="PRICE: Merton Call Price.", handler=calculate_me_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_me_put_price", description="PRICE: Merton Put Price.", handler=calculate_me_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})

        # 3. Greeks - BS (12 Tools)
        self.register_tool(name="calculate_bs_delta", description="GREEK: BS Delta.", handler=calculate_bs_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_call_delta", description="GREEK: BS Call Delta.", handler=calculate_bs_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_put_delta", description="GREEK: BS Put Delta.", handler=calculate_bs_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})

        self.register_tool(name="calculate_bs_gamma", description="GREEK: BS Gamma.", handler=calculate_bs_gamma, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        # Gamma is same for Call/Put
        
        self.register_tool(name="calculate_bs_theta", description="GREEK: BS Theta.", handler=calculate_bs_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_call_theta", description="GREEK: BS Call Theta.", handler=calculate_bs_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_put_theta", description="GREEK: BS Put Theta.", handler=calculate_bs_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        self.register_tool(name="calculate_bs_vega", description="GREEK: BS Vega.", handler=calculate_bs_vega, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        self.register_tool(name="calculate_bs_rho", description="GREEK: BS Rho.", handler=calculate_bs_rho, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_call_rho", description="GREEK: BS Call Rho.", handler=calculate_bs_rho, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_bs_put_rho", description="GREEK: BS Put Rho.", handler=calculate_bs_rho, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        # 4. Greeks - GK (12 Tools)
        self.register_tool(name="calculate_gk_delta", description="GREEK: GK Delta.", handler=calculate_gk_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_call_delta", description="GREEK: GK Call Delta.", handler=calculate_gk_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_put_delta", description="GREEK: GK Put Delta.", handler=calculate_gk_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        self.register_tool(name="calculate_gk_theta", description="GREEK: GK Theta.", handler=calculate_gk_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_call_theta", description="GREEK: GK Call Theta.", handler=calculate_gk_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="get_gk_put_theta", description="GREEK: GK Put Theta.", handler=calculate_gk_theta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "volatility": {"type": "number"}})
        
        # 5. Volatility
        self.register_tool(name="calculate_implied_volatility", description="VOL: Calculate IV.", handler=calculate_implied_volatility, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "call_price": {"type": "number"}})
        self.register_tool(name="get_bs_iv", description="VOL: BS IV.", handler=calculate_implied_volatility, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "interest": {"type": "number"}, "days": {"type": "number"}, "call_price": {"type": "number"}})

        # 6. Analysis & Probability (Phase 2)
        self.register_tool(name="calculate_put_call_parity", description="ANALYSIS: Parity Check.", handler=calculate_put_call_parity, parameters={"call_price": {"type": "number"}, "put_price": {"type": "number"}})
        self.register_tool(name="calculate_moneyness", description="ANALYSIS: Moneyness.", handler=calculate_moneyness, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}})
        self.register_tool(name="calculate_probability_itm", description="PROB: Prob ITM (Dual Delta).", handler=calculate_probability_itm, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="calculate_dual_delta", description="PROB: Dual Delta.", handler=calculate_dual_delta, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}})
        
        # 7. Simulation (Phase 2)
        self.register_tool(name="simulate_greek_scenario", description="SIM: Risk Simulation.", handler=simulate_greek_scenario, parameters={"underlying_start": {"type": "number"}, "underlying_end": {"type": "number"}, "steps": {"type": "number"}})

        # 8. Strategy & Advanced Greeks (Phase 3)
        self.register_tool(name="calculate_strategy_price", description="STRATEGY: Multi-leg.", handler=calculate_strategy_price, parameters={"legs": {"type": "array"}})
        
        self.register_tool(name="calculate_advanced_greeks", description="ADV: Vanna/Volmma.", handler=calculate_advanced_greeks, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "days": {"type": "number"}})
        self.register_tool(name="calculate_vanna", description="ADV: Vanna.", handler=calculate_vanna, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "days": {"type": "number"}})
        self.register_tool(name="calculate_vomma", description="ADV: Vomma.", handler=calculate_vomma, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "days": {"type": "number"}})
        self.register_tool(name="calculate_charm", description="ADV: Charm.", handler=calculate_charm, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "days": {"type": "number"}})
        self.register_tool(name="calculate_speed", description="ADV: Speed.", handler=calculate_speed, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "days": {"type": "number"}})
        
        self.register_tool(name="calculate_binary_price", description="EXOTIC: Binary Option.", handler=calculate_binary_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}})

        # 9. Structural (Phase 4)
        self.register_tool(name="calculate_american_price", description="STRUCTURAL: American Option.", handler=calculate_american_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}})
        self.register_tool(name="calculate_barrier_price", description="EXOTIC: Barrier Option.", handler=calculate_barrier_price, parameters={"underlying": {"type": "number"}, "strike": {"type": "number"}, "volatility": {"type": "number"}, "barrier": {"type": "number"}})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="mibian_server"))
    server = MibianServer()
    logger.info(f"Starting MibianServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
