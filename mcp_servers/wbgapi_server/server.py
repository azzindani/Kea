
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.wbgapi_server.tools.indicators import get_indicator_data, get_indicator_map
from mcp_servers.wbgapi_server.tools.economy import get_country_info, search_economies, get_region_list
from mcp_servers.wbgapi_server.tools.discovery import search_indicators, get_indicators_by_topic, get_topic_list
from mcp_servers.wbgapi_server.tools.dashboards import get_dashboard

logger = get_logger(__name__)

class WbgapiServer(MCPServer):
    """
    World Bank API (wbgapi) MCP Server.
    Focus: Global Development Data, Long-term Trends.
    """
    
    def __init__(self) -> None:
        super().__init__(name="wbgapi_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        
        # --- 1. INDICATOR TOOLS (Unrolled) ---
        # 30+ Tools
        
        INDICATORS = get_indicator_map()
        
        for name, code in INDICATORS.items():
            tool_name = f"get_{name}"
            desc = f"INDICATOR: Get '{name}' ({code}) for economies."
            
            async def ind_handler(args: dict, c=code) -> ToolResult:
                args["indicator_code"] = c
                return await get_indicator_data(args)
                
            self.register_tool(
                name=tool_name, description=desc, handler=ind_handler,
                parameters={
                    "economies": {"type": "array", "description": "List of country codes (e.g. ['USA', 'CHN']). Default: All."},
                    "mrv": {"type": "integer", "description": "Most Recent Values to fetch (Default 5)."}
                }
            )

        # Generic Indicator
        self.register_tool(
            name="get_indicator_data",
            description="BULK: Fetch data for ANY indicator code (e.g. 'NY.GDP.MKTP.CD').",
            handler=get_indicator_data,
            parameters={
                 "indicator_code": {"type": "string"},
                 "economies": {"type": "array"},
                 "mrv": {"type": "integer"}
            }
        )

        # --- 2. ECONOMY TOOLS ---
        self.register_tool(name="get_country_info", description="ECONOMY: Get info for countries.", handler=get_country_info, parameters={"country_codes": {"type": "array"}})
        self.register_tool(name="search_economies", description="ECONOMY: Search countries by name.", handler=search_economies, parameters={"query": {"type": "string"}})
        self.register_tool(name="get_region_list", description="ECONOMY: List all regions.", handler=get_region_list)

        # --- 3. DISCOVERY TOOLS ---
        self.register_tool(name="search_indicators", description="DISCOVERY: Search indicators by keyword.", handler=search_indicators, parameters={"query": {"type": "string"}})
        self.register_tool(name="get_indicators_by_topic", description="DISCOVERY: Browse Topic.", handler=get_indicators_by_topic, parameters={"topic_id": {"type": "integer"}})
        self.register_tool(name="get_topic_list", description="DISCOVERY: List all Topics.", handler=get_topic_list)

        # --- 4. DASHBOARD TOOLS ---
        dashboards = ["growth", "poverty", "climate", "tech"]
        for d in dashboards:
            name = f"get_{d}_dashboard"
            desc = f"DASHBOARD: Get {d.title()} indicators aggregated."
             
            async def d_handler(args: dict, dt=d) -> ToolResult:
                return await get_dashboard(args, dt)
            
            self.register_tool(
                name=name, description=desc, handler=d_handler,
                parameters={"economies": {"type": "array"}}
            )

        # --- 5. PHASE 2: SPECIALIZED & HISTORY ---
        
        from mcp_servers.wbgapi_server.tools.specialized import get_specialized_data, get_historical_data
        
        self.register_tool(
            name="get_gender_stats", description="SPECIAL: Get stats from Gender Database.",
            handler=lambda args: get_specialized_data(args, "gender"),
            parameters={"economies": {"type": "array"}}
        )
        self.register_tool(
            name="get_education_stats", description="SPECIAL: Get stats from Education Database.",
            handler=lambda args: get_specialized_data(args, "education"),
            parameters={"economies": {"type": "array"}}
        )
        self.register_tool(
            name="get_historical_data", description="HISTORY: Get 50-year trend for any indicator.",
            handler=get_historical_data,
            parameters={"indicator_code": {"type": "string"}, "economies": {"type": "array"}}
        )

        # --- 6. PHASE 2: AGGREGATES ---
        
        from mcp_servers.wbgapi_server.tools.aggregates import get_region_data, get_income_level_data
        
        self.register_tool(
            name="get_region_data", description="AGGREGATE: Get data for all Regions (EAS, SAS, etc).",
            handler=get_region_data, parameters={"indicator_code": {"type": "string"}}
        )
        self.register_tool(
            name="get_income_level_data", description="AGGREGATE: Get data for Income Groups (HIC, LIC, etc).",
            handler=get_income_level_data, parameters={"indicator_code": {"type": "string"}}
        )

        self.register_tool(
            name="get_income_level_data", description="AGGREGATE: Get data for Income Groups (HIC, LIC, etc).",
            handler=get_income_level_data, parameters={"indicator_code": {"type": "string"}}
        )

        # --- 7. PHASE 3: SDGs & MICRO-DASHBOARDS ---
        
        from mcp_servers.wbgapi_server.tools.sdg import get_sdg_data, get_poverty_equity_data
        from mcp_servers.wbgapi_server.tools.granular_dashboards import get_granular_dashboard
        
        self.register_tool(
            name="get_sdg_data", description="SDG: Get Key Indicators for a specific Goal.",
            handler=get_sdg_data, parameters={"goal": {"type": "integer"}, "economies": {"type": "array"}}
        )
        self.register_tool(
            name="get_poverty_equity_data", description="WT: Get Deep Poverty & Equity stats (DB 24/2).",
            handler=get_poverty_equity_data, parameters={"economies": {"type": "array"}}
        )
        
        mdashes = ["food_security", "digital", "energy"]
        for md in mdashes:
            name = f"get_{md}_dashboard"
            desc = f"DASHBOARD: Get {md.replace('_', ' ').title()} indicators."
            
            async def md_handler(args: dict, m=md) -> ToolResult:
                return await get_granular_dashboard(args, m)
                
            self.register_tool(
                name=name, description=desc, handler=md_handler,
                parameters={"economies": {"type": "array"}}
            )

        # --- 8. PHASE 4: DEEP DEEP DIVE (Debt, Governance, Metadata) ---
        
        from mcp_servers.wbgapi_server.tools.debt import get_debt_stats
        from mcp_servers.wbgapi_server.tools.governance import get_governance_data
        from mcp_servers.wbgapi_server.tools.metadata_deep import get_indicator_metadata
        
        self.register_tool(
            name="get_debt_stats", description="DEBT: Get International Debt (IDS, DB 6).",
            handler=get_debt_stats, parameters={"economies": {"type": "array"}}
        )
        self.register_tool(
            name="get_governance_data", description="GOVERNANCE: Get Corruption/Stability (WGI, DB 3).",
            handler=get_governance_data, parameters={"economies": {"type": "array"}}
        )
        self.register_tool(
            name="get_indicator_metadata", description="META: Get Definitions & Source Notes.",
            handler=get_indicator_metadata, parameters={"indicator_code": {"type": "string"}}
        )

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="wbgapi_server"))
    server = WbgapiServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
