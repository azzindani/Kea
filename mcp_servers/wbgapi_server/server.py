
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.wbgapi_server.tools import (
    indicators, economy, discovery, dashboards, specialized, aggregates,
    sdg, granular_dashboards, debt, governance, metadata_deep
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("wbgapi_server", dependencies=["wbgapi", "pandas"])

async def run_op(op_func, diff_args=None, **kwargs):
    """
    Helper to run legacy tool ops.
    diff_args: dict of overrides/additions to kwargs before passing to op.
    """
    try:
        # Combine args
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        # The tools expect a single 'arguments' dict.
        result = await op_func(final_args)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
        
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# --- 1. INDICATOR TOOLS ---
INDICATORS = indicators.get_indicator_map()

@mcp.tool()
async def get_indicator_data(indicator_code: str, economies: list[str] = None, mrv: int = 5) -> str:
    """FETCHES indicator data. [ACTION]
    
    [RAG Context]
    A premier "Super Tool" for global economic research. It retrieves historical time-series data for any of the 16,000+ indicators in the World Bank Open Data catalog.
    
    How to Use:
    - 'indicator_code': The unique WB ID (e.g., 'NY.GDP.MKTP.CD' for GDP, 'SP.POP.TOTL' for Population).
    - 'economies': List of ISO3 codes (e.g., ['USA', 'CHN', 'GBR']) or regions.
    - 'mrv': Most Recent Values. Number of recent periods to fetch.
    
    Keywords: world bank data, economic indicator, gdp fetch, macro stats, time series.
    """
    return await run_op(indicators.get_indicator_data, indicator_code=indicator_code, economies=economies, mrv=mrv)

# --- 2. ECONOMY TOOLS ---
@mcp.tool()
async def get_country_info(country_codes: list[str] = None) -> str:
    """FETCHES country info. [ACTION]
    
    [RAG Context]
    Get metadata for specific countries.
    Returns JSON string.
    """
    return await run_op(economy.get_country_info, country_codes=country_codes)

@mcp.tool()
async def search_economies(query: str) -> str:
    """SEARCHES economies. [ACTION]
    
    [RAG Context]
    Search for countries/economies by name.
    Returns list of matches.
    """
    return await run_op(economy.search_economies, query=query)

@mcp.tool()
async def get_region_list() -> str:
    """LISTS regions. [ACTION]
    
    [RAG Context]
    Get list of all World Bank regions.
    Returns list string.
    """
    return await run_op(economy.get_region_list)

# --- 3. DISCOVERY TOOLS ---
@mcp.tool()
async def search_indicators(query: str) -> str:
    """SEARCHES indicators. [ACTION]
    
    [RAG Context]
    A discovery "Super Tool" for navigating the massive World Bank database. It identifies indicator codes based on natural language keywords.
    
    How to Use:
    - Input 'query' such as "renewable energy", "literacy rate", or "inflation".
    - Returns a list of matching indicator titles and their corresponding codes (IDs) for use in 'get_indicator_data'.
    
    Keywords: indicator search, wb catalog, find metrics, research discovery.
    """
    return await run_op(discovery.search_indicators, query=query)

@mcp.tool()
async def get_indicators_by_topic(topic_id: int) -> str:
    """FETCHES topic indicators. [ACTION]
    
    [RAG Context]
    Get all indicators within a specific topic.
    Returns list string.
    """
    return await run_op(discovery.get_indicators_by_topic, topic_id=topic_id)

@mcp.tool()
async def get_topic_list() -> str:
    """LISTS topics. [ACTION]
    
    [RAG Context]
    Get list of all indicator topics.
    Returns list string.
    """
    return await run_op(discovery.get_topic_list)

# --- 4. DASHBOARD TOOLS ---
@mcp.tool()
async def get_growth_dashboard(economies: list[str] = None) -> str:
    """GENERATES Growth db. [ACTION]
    
    [RAG Context]
    A high-level "Super Tool" for macro-economic profiling. It aggregates a suite of growth-related indicators (GDP growth, GNI per capita, Inflation) into a structured summary report.
    
    How to Use:
    - Provide a list of country codes to compare their recent economic performance.
    - Essential for rapid country risk assessment and investment research.
    
    Keywords: growth report, economic health, gdp summary, country profile.
    """
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "growth"}, economies=economies)

@mcp.tool()
async def get_poverty_dashboard(economies: list[str] = None) -> str:
    """GENERATES Poverty db. [ACTION]
    
    [RAG Context]
    Get aggregated Poverty indicators.
    Returns dashboard string.
    """
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "poverty"}, economies=economies)

@mcp.tool()
async def get_climate_dashboard(economies: list[str] = None) -> str:
    """GENERATES Climate db. [ACTION]
    
    [RAG Context]
    Get aggregated Climate indicators.
    Returns dashboard string.
    """
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "climate"}, economies=economies)

@mcp.tool()
async def get_tech_dashboard(economies: list[str] = None) -> str:
    """GENERATES Tech db. [ACTION]
    
    [RAG Context]
    Get aggregated Technology indicators.
    Returns dashboard string.
    """
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "tech"}, economies=economies)

# --- 5. SPECIALIZED & HISTORY ---
# --- 5. SPECIALIZED & HISTORY ---
@mcp.tool()
async def get_gender_stats(economies: list[str] = None) -> str:
    """FETCHES Gender stats. [ACTION]
    
    [RAG Context]
    Get specialized Gender Database indicators.
    Returns data table.
    """
    return await run_op(specialized.get_specialized_data, diff_args={"db_type": "gender"}, economies=economies)

@mcp.tool()
async def get_education_stats(economies: list[str] = None) -> str:
    """FETCHES Education stats. [ACTION]
    
    [RAG Context]
    Get specialized Education Database indicators.
    Returns data table.
    """
    return await run_op(specialized.get_specialized_data, diff_args={"db_type": "education"}, economies=economies)

@mcp.tool()
async def get_historical_data(indicator_code: str, economies: list[str] = None) -> str:
    """FETCHES history. [ACTION]
    
    [RAG Context]
    Get 50-year trend data for an indicator.
    Returns time series data.
    """
    return await run_op(specialized.get_historical_data, indicator_code=indicator_code, economies=economies)

# --- 6. AGGREGATES ---
@mcp.tool()
async def get_region_data(indicator_code: str) -> str:
    """FETCHES region data. [ACTION]
    
    [RAG Context]
    Get indicator data aggregated by Region.
    Returns data table.
    """
    return await run_op(aggregates.get_region_data, indicator_code=indicator_code)

@mcp.tool()
async def get_income_level_data(indicator_code: str) -> str:
    """FETCHES income data. [ACTION]
    
    [RAG Context]
    Get indicator data aggregated by Income Group.
    Returns data table.
    """
    return await run_op(aggregates.get_income_level_data, indicator_code=indicator_code)

# --- 7. SDGs & MICRO-DASHBOARDS ---
@mcp.tool()
async def get_sdg_data(goal: int, economies: list[str] = None) -> str:
    """FETCHES SDG data. [ACTION]
    
    [RAG Context]
    A specialized "Super Tool" for tracking the UN Sustainable Development Goals. It filters the global database for indicators specifically mapped to one of the 17 SDG goals.
    
    How to Use:
    - 'goal': An integer from 1 to 17 (e.g., 1 for No Poverty, 13 for Climate Action).
    - Perfect for ESG (Environmental, Social, and Governance) analysis and developmental impact studies.
    
    Keywords: esg metrics, sustainable development, un goals, impact investing.
    """
    return await run_op(sdg.get_sdg_data, goal=goal, economies=economies)

@mcp.tool()
async def get_poverty_equity_data(economies: list[str] = None) -> str:
    """FETCHES Poverty Equity. [ACTION]
    
    [RAG Context]
    Get Deep Poverty & Equity stats (DB 24).
    Returns data table.
    """
    return await run_op(sdg.get_poverty_equity_data, economies=economies)

@mcp.tool()
async def get_food_security_dashboard(economies: list[str] = None) -> str:
    """GENERATES FoodSecurity db. [ACTION]
    
    [RAG Context]
    Get Food Security indicators.
    Returns dashboard string.
    """
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "food_security"}, economies=economies)

@mcp.tool()
async def get_digital_dashboard(economies: list[str] = None) -> str:
    """GENERATES Digital db. [ACTION]
    
    [RAG Context]
    Get Digital/Technology indicators.
    Returns dashboard string.
    """
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "digital"}, economies=economies)

@mcp.tool()
async def get_energy_dashboard(economies: list[str] = None) -> str:
    """GENERATES Energy db. [ACTION]
    
    [RAG Context]
    Get Energy indicators.
    Returns dashboard string.
    """
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "energy"}, economies=economies)

# --- 8. DEEP DIVE ---
@mcp.tool()
async def get_debt_stats(economies: list[str] = None) -> str:
    """FETCHES Debt stats. [ACTION]
    
    [RAG Context]
    Get International Debt statistics (IDS).
    Returns data table.
    """
    return await run_op(debt.get_debt_stats, economies=economies)

@mcp.tool()
async def get_governance_data(economies: list[str] = None) -> str:
    """FETCHES Governance stats. [ACTION]
    
    [RAG Context]
    Get Worldwide Governance Indicators (WGI).
    Returns data table.
    """
    return await run_op(governance.get_governance_data, economies=economies)

@mcp.tool()
async def get_indicator_metadata(indicator_code: str) -> str:
    """FETCHES meta. [ACTION]
    
    [RAG Context]
    Get definitions and source notes for indicator.
    Returns metadata string.
    """
    return await run_op(metadata_deep.get_indicator_metadata, indicator_code=indicator_code)


# Register dynamic shortcuts
for name, code in INDICATORS.items():
    tool_name = f"get_{name}"
    desc = f"INDICATOR: Get '{name}' ({code}) for economies."
    
    # We must bind 'c=code' to capture the value in the loop
    def make_handler(c=code):
        async def handler(economies: list[str] = None, mrv: int = 5):
            return await run_op(indicators.get_indicator_data, indicator_code=c, economies=economies, mrv=mrv)
        return handler
    
    mcp.add_tool(name=tool_name, description=desc, fn=make_handler())

if __name__ == "__main__":
    mcp.run()


# ==========================================
# Compatibility Layer for Tests
# ==========================================
class WbgapiServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

