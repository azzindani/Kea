
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.wbgapi_server.tools.indicators import INDICATORS

logger = get_logger(__name__)

# Add new mappings here or import
# Granular definitions
THEMES = {
    "food_security": ["AG.LND.ARBL.ZS", "AG.PRD.FOOD.XD", "AG.YLD.CREL.KG", "SN.ITK.DEFC.ZS"], # Arable, Food Index, Yield, Undernourishment
    "digital": ["IT.NET.USER.ZS", "IT.CEL.SETS.P2", "IT.NET.BBND.P2"], # Internet, Mobile, Broadband
    "energy": ["EG.ELC.ACCS.ZS", "EG.FEC.RNEW.ZS", "EG.USE.PCAP.KG.OE", "EN.ATM.CO2E.KT"] # Access, Renewable, Use, CO2
}

async def get_granular_dashboard(arguments: dict, theme: str) -> ToolResult:
    """
    Get a specific micro-dashboard.
    theme: "food_security", "digital", "energy"
    """
    economies = arguments.get("economies")
    mrv = arguments.get("mrv", 1)
    
    if theme not in THEMES:
        return ToolResult(isError=True, content=[TextContent(text="Invalid theme")])
        
    codes = THEMES[theme]
    
    try:
        df = wb.data.DataFrame(codes, economy=economies, mrv=mrv, labels=True)
        return ToolResult(content=[TextContent(text=f"### Dashboard: {theme.replace('_', ' ').title()}\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
