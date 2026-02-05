
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

# SDG Codes (Sample)
SDG_MAP = {
    "poverty_ratio": "SI.POV.DDAY", # Goal 1
    "undernourishment": "SN.ITK.DEFC.ZS", # Goal 2
    "maternal_mortality": "SH.STA.MMRT", # Goal 3
    "primary_completion": "SE.PRM.CMPT.ZS", # Goal 4
    "women_parliament": "SG.GEN.PARL.ZS", # Goal 5
    "water_access": "SH.H2O.BASW.ZS", # Goal 6
    "clean_energy": "EG.FEC.RNEW.ZS", # Goal 7
    "gdp_per_capita_growth": "NY.GDP.PCAP.KD.ZG", # Goal 8
    "manufacturing_value": "NV.IND.MANF.ZS" # Goal 9
}

async def get_sdg_data(arguments: dict) -> ToolResult:
    """
    Get Sustainable Development Goal (SDG) Data (DB=46 generally, but often in WDI).
    SDG DB is 46, but WDI covers most. We will use specialized if needed.
    """
    economies = arguments.get("economies")
    goal = arguments.get("goal") # 1-17
    
    # Simple logic: Fetch all indicator codes for that goal if we had a mapping.
    # For now, let's just fetch a specific key indicator for that goal.
    
    # Actually, better tool: get_sdg_dashboard(goal_number)
    
    # Let's pivot to fetching strictly from the SDG database if possible to be "Specialized"
    # But wbgapi doesn't easily map "Goal 1" to "List of indicators".
    # I will just expose key mapped indicators.
    
    try:
        codes = list(SDG_MAP.values())
        # Querying them all might be heavy. Let's do it.
        # DB=46 is dedicated to SDGs.
        df = wb.data.DataFrame(codes, economy=economies, mrv=1, labels=True) # Try default DB first as they are often there.
        
        return ToolResult(content=[TextContent(text=f"### Overview: SDGs (Selected Indicators)\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_poverty_equity_data(arguments: dict) -> ToolResult:
    """
    Get Poverty & Equity Data (DB=24).
    """
    economies = arguments.get("economies")
    # Sample vars
    # Gini, Poverty Gap, Headcount
    codes = ["SI.POV.GINI", "SI.POV.DDAY", "SI.POV.GAPS", "SI.DST.FRST.20"]
    
    try:
        df = wb.data.DataFrame(codes, economy=economies, mrv=1, db=2, labels=True) # WDI usually has these updated.
        if df.empty:
            # Try DB 24
             df = wb.data.DataFrame(codes, economy=economies, mrv=1, db=24, labels=True)
             
        return ToolResult(content=[TextContent(text=f"### Poverty & Equity (Key Stats)\n\n{df.to_markdown()}")])
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])
