
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_region_data(arguments: dict) -> ToolResult:
    """
    Get indicator data for entire Regions (aggregates).
    """
    indicator = arguments.get("indicator_code")
    try:
        # 'aggregates' returns data for region codes like 'EAS', 'SAS', 'LCN'
        # wb.region.members returns countries in region.
        # But we want the aggregate value itself (if available).
        # Most WDI indicators have values for region codes.
        
        # Get list of all region codes
        regions = wb.region.list() # returns generator of dicts
        region_codes = [r['code'] for r in regions]
        
        df = wb.data.DataFrame(indicator, economy=region_codes, mrv=1, labels=True)
        
        return ToolResult(content=[TextContent(text=f"### Regional Aggregates: {indicator}\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_income_level_data(arguments: dict) -> ToolResult:
    """
    Get indicator data for Income Groups (High, Low, etc).
    """
    indicator = arguments.get("indicator_code")
    try:
        # Income codes: HIC, LIC, LMC, UMC, etc.
        # Use .list() which returns a generator of objects (dictionaries or objects)
        income_gen = wb.income.list()
        
        # We need the 'id' or 'code' from these objects. 
        # wb.income.list() usually yields simple objects with 'id', 'value' etc.
        income_codes = [i['id'] for i in income_gen]
        
        df = wb.data.DataFrame(indicator, economy=income_codes, mrv=1, labels=True)
        return ToolResult(content=[TextContent(text=f"### Income Group Aggregates: {indicator}\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
