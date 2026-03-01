
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

# WGI Mappings (DB=3)
# Codes often: CC.EST (Control of Corruption), RL.EST (Rule of Law)
# Estimate ranges -2.5 (weak) to 2.5 (strong)
WGI_MAP = {
    "control_of_corruption": "CC.EST",
    "rule_of_law": "RL.EST",
    "regulatory_quality": "RQ.EST",
    "government_effectiveness": "GE.EST",
    "political_stability": "PV.EST",
    "voice_and_accountability": "VA.EST"
}

async def get_governance_data(arguments: dict) -> ToolResult:
    """
    Get Worldwide Governance Indicators (WGI) - DB 3.
    Range: -2.5 (Weak) to 2.5 (Strong).
    """
    economies = arguments.get("economies")
    mrv = arguments.get("mrv", 5)
    
    try:
        codes = list(WGI_MAP.values())
        df = wb.data.DataFrame(codes, economy=economies, mrv=mrv, db=3, labels=True)
        
        return ToolResult(content=[TextContent(text=f"### Governance Indicators (WGI) [-2.5 to 2.5]\n\n{df.to_markdown()}")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
