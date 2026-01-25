
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd

logger = get_logger(__name__)

async def get_country_info(arguments: dict) -> ToolResult:
    """Get info for specific countries."""
    ids = arguments.get("country_codes") 
    try:
        # wb.economy.info returns a generator or list of objects
        info = wb.economy.info(ids)
        
        # Convert to list of dicts for DataFrame
        data = [i.__dict__ for i in info]
        if not data:
             return ToolResult(content=[TextContent(text="No info found.")])
             
        # Clean up (remove private attrs if any)
        clean_data = [{k:v for k,v in d.items() if not k.startswith('_')} for d in data]
        
        return ToolResult(content=[TextContent(text=f"### Economy Info\n\n{pd.DataFrame(clean_data).to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def search_economies(arguments: dict) -> ToolResult:
    """Search for country codes by name."""
    query = arguments.get("query")
    try:
        # wb.economy.coder returns dict of Name -> Code
        # actually wb.economy.coder(query) isn't standard function.
        # usually wb.economy.info() prints.
        # Best way: Iterate all economies filtering by name? or use source logic.
        
        # Simpler: Get all economies and filter dataframe
        df = pd.DataFrame(wb.economy.list())
        # df columns: id, value, aggregate, longitude, latitude, region, adminregion, lendingType, incomeLevel, capitalCity
        
        mask = df['value'].str.contains(query, case=False, na=False)
        result = df[mask]
        
        return ToolResult(content=[TextContent(text=f"### Search Results: '{query}'\n\n{result.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_region_list(arguments: dict) -> ToolResult:
    """List all regions."""
    try:
        df = pd.DataFrame(wb.region.list())
        return ToolResult(content=[TextContent(text=f"### Regions\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
