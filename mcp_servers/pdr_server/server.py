
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.pdr_server.tools.famafrench import get_fama_french_data, get_ff_map
from mcp_servers.pdr_server.tools.market_global import get_stooq_data, get_tsp_fund_data
from mcp_servers.pdr_server.tools.dashboards import get_factor_dashboard, get_global_factors_dashboard

logger = get_logger(__name__)

class PdrServer(MCPServer):
    """
    Pandas Datareader (PDR) MCP Server.
    Focus: Academic Finance, Global Macro, Indices.
    """
    
    def __init__(self) -> None:
        super().__init__(name="pdr_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        
        # --- 1. ACADEMIC ENGINE (Fama-French) ---
        # Unroll 40+ Datasets
        
        FF_DATASETS = get_ff_map()
        
        for name, code in FF_DATASETS.items():
            tool_name = f"get_{name}"
            desc = f"ACADEMIC: Get Fama-French '{name}' - {code}."
            
            async def ff_handler(args: dict, c=code) -> ToolResult:
                return await get_fama_french_data(args, c)
                
            self.register_tool(
                name=tool_name, description=desc, handler=ff_handler,
                parameters={
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"}
                }
            )

        # Generic FF Tool
        self.register_tool(
            name="get_fama_french_dataset",
            description="ACADEMIC: Get ANY Fama-French dataset by code.",
            handler=get_fama_french_data,
            parameters={"dataset_name": {"type": "string"}, "start_date": {"type": "string"}}
        )

        # --- 2. MARKET ENGINE (Stooq, TSP) ---
        self.register_tool(
            name="get_stooq_data",
            description="MARKET: Get Index/ETF/Currency data from Stooq (lists supported).",
            handler=get_stooq_data,
            parameters={"symbols": {"type": "array"}, "start_date": {"type": "string"}}
        )
        self.register_tool(
            name="get_tsp_fund_data",
            description="INSTITUTION: Get Thrift Savings Plan (TSP) Fund data.",
            handler=get_tsp_fund_data
        )

        # --- 3. DASHBOARDS ---
        self.register_tool(
            name="get_factor_dashboard",
            description="DASHBOARD: US Factors (5-Factor + Momentum).",
            handler=get_factor_dashboard
        )
        self.register_tool(
            name="get_global_factors_dashboard",
            description="DASHBOARD: Global Factors (Dev, Emerging, Europe, Japan).",
            handler=get_global_factors_dashboard
        )
        
        # --- 4. PHASE 2: SYMBOLS & CENTRAL BANK ---
        
        from mcp_servers.pdr_server.tools.market_symbols import get_nasdaq_symbol_list
        from mcp_servers.pdr_server.tools.central_bank import get_bank_of_canada_data
        
        self.register_tool(
            name="get_nasdaq_symbol_list", description="DISCOVERY: Get all Nasdaq/NYSE traded symbols.",
            handler=get_nasdaq_symbol_list, parameters={"query": {"type": "string"}}
        )
        self.register_tool(
            name="get_bank_of_canada_data", description="MACRO: Get Bank of Canada Rates/FX.",
            handler=get_bank_of_canada_data, parameters={"symbols": {"type": "array"}, "start_date": {"type": "string"}}
        )

        # --- 5. PHASE 3: COMMERCIAL & ADVANCED DASHBOARDS ---
        
        from mcp_servers.pdr_server.tools.commercial import get_tiingo_data, get_alphavantage_data
        from mcp_servers.pdr_server.tools.dashboards import get_industry_health_dashboard, get_liquidity_dashboard
        from mcp_servers.pdr_server.tools.market_global import get_moex_data
        
        self.register_tool(
            name="get_tiingo_data", description="COMMERCIAL: Get Tiingo Data (API Key required).",
            handler=get_tiingo_data, parameters={"symbols": {"type": "array"}, "api_key": {"type": "string"}}
        )
        self.register_tool(
            name="get_alphavantage_data", description="COMMERCIAL: Get AlphaVantage Data (API Key required).",
            handler=get_alphavantage_data, parameters={"symbols": {"type": "array"}, "api_key": {"type": "string"}}
        )
        self.register_tool(
            name="get_industry_health_dashboard", description="DASHBOARD: 49 Industry Sectors Health.",
            handler=get_industry_health_dashboard
        )
        self.register_tool(
            name="get_liquidity_dashboard", description="DASHBOARD: Market Liquidity Factors.",
            handler=get_liquidity_dashboard
        )
        self.register_tool(
            name="get_moex_data", description="MARKET: Moscow Exchange Data.",
            handler=get_moex_data, parameters={"symbols": {"type": "array"}}
        )

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="pdr_server"))
    server = PdrServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
