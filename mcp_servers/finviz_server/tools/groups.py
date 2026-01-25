
from finvizfinance.group.overview import Overview
from finvizfinance.group.valuation import Valuation
from finvizfinance.group.performance import Performance
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_group_data(arguments: dict, mode: str) -> ToolResult:
    """
    Get Group Data (Sector/Industry/Country).
    mode: "overview", "valuation", "performance"
    """
    group_by = arguments.get("group_by", "Sector") # Sector, Industry, Country
    
    try:
        if mode == "overview":
            obj = Overview()
        elif mode == "valuation":
            obj = Valuation()
        elif mode == "performance":
            obj = Performance()
        else:
            return ToolResult(isError=True, content=[TextContent(text="Invalid mode")])
            
        # screener_view(group='Sector', order='Name')
        df = obj.screener_view(group=group_by)
        
        return ToolResult(content=[TextContent(text=f"### Group: {group_by} ({mode})\n\n{df.to_markdown()}")])
        
    except Exception as e:
        logger.error(f"Group error {group_by}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
