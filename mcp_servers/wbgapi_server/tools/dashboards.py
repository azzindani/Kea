
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
import pandas as pd
from mcp_servers.wbgapi_server.tools.indicators import INDICATORS

logger = get_logger(__name__)

# Dashboard mappings
DASHBOARDS = {
    "growth": ["gdp_growth", "gdp_per_capita", "inflation", "unemployment_rate"],
    "poverty": ["poverty_headcount", "gini_index", "literacy_rate", "life_expectancy"],
    "climate": ["co2_emissions", "renewable_energy", "forest_area", "electricity_access"],
    "tech": ["internet_usage", "mobile_subscriptions", "high_tech_exports"]
}

async def get_dashboard(arguments: dict, dashboard_type: str) -> ToolResult:
    """
    Get a thematic dashboard for countries.
    dashboard_type: "growth", "poverty", "climate", "tech"
    """
    economies = arguments.get("economies")
    mrv = arguments.get("mrv", 1) # Just the latest snapshot usually
    
    if dashboard_type not in DASHBOARDS:
        return ToolResult(isError=True, content=[TextContent(text="Invalid dashboard type")])
        
    keys = DASHBOARDS[dashboard_type]
    codes = [INDICATORS.get(k, k) for k in keys if k in INDICATORS] # Resolve friendly names
    
    try:
        # Fetch all codes at once
        df = wb.data.DataFrame(codes, economy=economies, mrv=mrv, labels=True)
        
        if df is None or df.empty:
            return ToolResult(content=[TextContent(text="No data found.")])
            
        return ToolResult(content=[TextContent(text=f"### Dashboard: {dashboard_type.title()} (Latest Values)\n\n{df.to_markdown()}")])
        
    except Exception as e:
        logger.error(f"Dashboard error {dashboard_type}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
