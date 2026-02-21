
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

# IDS Mappings (DB=6 usually)
DEBT_MAP = {
    "external_debt_stocks": "DT.DOD.DECT.CD",
    "debt_service_ppg": "DT.AMT.DPPG.CD", # Principal repayments
    "debt_service_percent_exports": "DT.TDS.DECT.EX.ZS",
    "fdi_net_inflows_debt": "BX.KLT.DINV.CD.DT",
    "multilateral_debt": "DT.DOD.MLAT.CD"
}

async def get_debt_stats(arguments: dict) -> ToolResult:
    """
    Get International Debt Statistics (IDS) - DB 6.
    """
    economies = arguments.get("economies")
    mrv = arguments.get("mrv", 5)
    
    # Check if we need to switch DB context.
    # WDI (DB 2) often contains these too.
    # But IDS (DB 6) is the source.
    # We will try DB 6.
    
    try:
        codes = list(DEBT_MAP.values())
        df = wb.data.DataFrame(codes, economy=economies, mrv=mrv, db=6, labels=True)
        
        return ToolResult(content=[TextContent(text=f"### International Debt Statistics (Latest {mrv} Years)\n\n{df.to_markdown()}")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
