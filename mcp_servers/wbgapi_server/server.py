
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    indicators, economy, discovery, dashboards, specialized, aggregates,
    sdg, granular_dashboards, debt, governance, metadata_deep
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
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
    """BULK: Fetch data for ANY indicator code (e.g. 'NY.GDP.MKTP.CD')."""
    return await run_op(indicators.get_indicator_data, indicator_code=indicator_code, economies=economies, mrv=mrv)

# --- 2. ECONOMY TOOLS ---
@mcp.tool()
async def get_country_info(country_codes: list[str] = None) -> str:
    """ECONOMY: Get info for countries."""
    return await run_op(economy.get_country_info, country_codes=country_codes)

@mcp.tool()
async def search_economies(query: str) -> str:
    """ECONOMY: Search countries by name."""
    return await run_op(economy.search_economies, query=query)

@mcp.tool()
async def get_region_list() -> str:
    """ECONOMY: List all regions."""
    return await run_op(economy.get_region_list)

# --- 3. DISCOVERY TOOLS ---
@mcp.tool()
async def search_indicators(query: str) -> str:
    """DISCOVERY: Search indicators by keyword."""
    return await run_op(discovery.search_indicators, query=query)

@mcp.tool()
async def get_indicators_by_topic(topic_id: int) -> str:
    """DISCOVERY: Browse Topic."""
    return await run_op(discovery.get_indicators_by_topic, topic_id=topic_id)

@mcp.tool()
async def get_topic_list() -> str:
    """DISCOVERY: List all Topics."""
    return await run_op(discovery.get_topic_list)

# --- 4. DASHBOARD TOOLS ---
@mcp.tool()
async def get_growth_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Growth indicators aggregated."""
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "growth"}, economies=economies)

@mcp.tool()
async def get_poverty_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Poverty indicators aggregated."""
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "poverty"}, economies=economies)

@mcp.tool()
async def get_climate_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Climate indicators aggregated."""
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "climate"}, economies=economies)

@mcp.tool()
async def get_tech_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Tech indicators aggregated."""
    return await run_op(dashboards.get_dashboard, diff_args={"dashboard_type": "tech"}, economies=economies)

# --- 5. SPECIALIZED & HISTORY ---
@mcp.tool()
async def get_gender_stats(economies: list[str] = None) -> str:
    """SPECIAL: Get stats from Gender Database."""
    return await run_op(specialized.get_specialized_data, diff_args={"db_type": "gender"}, economies=economies)

@mcp.tool()
async def get_education_stats(economies: list[str] = None) -> str:
    """SPECIAL: Get stats from Education Database."""
    return await run_op(specialized.get_specialized_data, diff_args={"db_type": "education"}, economies=economies)

@mcp.tool()
async def get_historical_data(indicator_code: str, economies: list[str] = None) -> str:
    """HISTORY: Get 50-year trend for any indicator."""
    return await run_op(specialized.get_historical_data, indicator_code=indicator_code, economies=economies)

# --- 6. AGGREGATES ---
@mcp.tool()
async def get_region_data(indicator_code: str) -> str:
    """AGGREGATE: Get data for all Regions (EAS, SAS, etc)."""
    return await run_op(aggregates.get_region_data, indicator_code=indicator_code)

@mcp.tool()
async def get_income_level_data(indicator_code: str) -> str:
    """AGGREGATE: Get data for Income Groups (HIC, LIC, etc)."""
    return await run_op(aggregates.get_income_level_data, indicator_code=indicator_code)

# --- 7. SDGs & MICRO-DASHBOARDS ---
@mcp.tool()
async def get_sdg_data(goal: int, economies: list[str] = None) -> str:
    """SDG: Get Key Indicators for a specific Goal."""
    return await run_op(sdg.get_sdg_data, goal=goal, economies=economies)

@mcp.tool()
async def get_poverty_equity_data(economies: list[str] = None) -> str:
    """WT: Get Deep Poverty & Equity stats (DB 24/2)."""
    return await run_op(sdg.get_poverty_equity_data, economies=economies)

@mcp.tool()
async def get_food_security_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Food Security indicators."""
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "food_security"}, economies=economies)

@mcp.tool()
async def get_digital_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Digital indicators."""
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "digital"}, economies=economies)

@mcp.tool()
async def get_energy_dashboard(economies: list[str] = None) -> str:
    """DASHBOARD: Get Energy indicators."""
    return await run_op(granular_dashboards.get_granular_dashboard, diff_args={"dashboard_type": "energy"}, economies=economies)

# --- 8. DEEP DIVE ---
@mcp.tool()
async def get_debt_stats(economies: list[str] = None) -> str:
    """DEBT: Get International Debt (IDS, DB 6)."""
    return await run_op(debt.get_debt_stats, economies=economies)

@mcp.tool()
async def get_governance_data(economies: list[str] = None) -> str:
    """GOVERNANCE: Get Corruption/Stability (WGI, DB 3)."""
    return await run_op(governance.get_governance_data, economies=economies)

@mcp.tool()
async def get_indicator_metadata(indicator_code: str) -> str:
    """META: Get Definitions & Source Notes."""
    return await run_op(metadata_deep.get_indicator_metadata, indicator_code=indicator_code)


# Register dynamic shortcuts
for name, code in INDICATORS.items():
    tool_name = f"get_{name}"
    desc = f"INDICATOR: Get '{name}' ({code}) for economies."
    
    # We must bind 'c=code' to capture the value in the loop
    async def make_ind_handler(c=code):
        async def handler(economies: list[str] = None, mrv: int = 5):
            return await run_op(indicators.get_indicator_data, indicator_code=c, economies=economies, mrv=mrv)
        return handler
    
    mcp.tool(name=tool_name, description=desc)(make_ind_handler())

if __name__ == "__main__":
    mcp.run()