
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

# Specialized Maps
GENDER_MAP = {
    "female_labor_participation": "SL.TLF.CACT.FE.ZS",
    "wage_gap": "SL.TLF.WAGE.FE.ZS", # Check availability
    "female_ownership": "IC.FRM.FEMO.ZS",
    "school_enrollment_secondary_female": "SE.SEC.ENRR.FE"
}

EDUCATION_MAP = {
    "literacy_adult": "SE.ADT.LITR.ZS",
    "primary_completion": "SE.PRM.CMPT.ZS",
    "tertiary_enrollment": "SE.TER.ENRR",
    "pupil_teacher_ratio": "SE.PRM.ENRL.TC.ZS"
}

async def get_specialized_data(arguments: dict, topic: str) -> ToolResult:
    """
    Get data from specialized databases.
    topic: "gender", "education"
    """
    economies = arguments.get("economies")
    
    try:
        if topic == "gender":
            db_id = 14 # Gender Statistics
            codes = list(GENDER_MAP.values())
        elif topic == "education":
            db_id = 12 # Education Statistics
            codes = list(EDUCATION_MAP.values())
        else:
            return ToolResult(isError=True, content=[TextContent(text="Invalid topic")])
        
        # Switch DB context implies we pass db=ID to query, OR change default.
        # wbgapi methods usually accept `db` argument.
        
        # However, `wb.data.DataFrame` accepts `db`.
        df = wb.data.DataFrame(codes, economy=economies, mrv=1, db=db_id, labels=True)
        
        return ToolResult(content=[TextContent(text=f"### Specialized: {topic.title()} Stats (Latest)\n\n{df.to_markdown()}")])
        
    except Exception as e:
        logger.error(f"Specialized error {topic}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_historical_data(arguments: dict) -> ToolResult:
    """
    Get 50-year history for an indicator.
    """
    code = arguments.get("indicator_code")
    economies = arguments.get("economies")
    
    try:
        # Fetch 50 years
        df = wb.data.DataFrame(code, economy=economies, time=range(1970, 2024), labels=True)
        # Transpose might be better for reading if single country
        if len(df) == 1:
            df = df.T
            
        return ToolResult(content=[TextContent(text=f"### History: {code} (1970-2023)\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
