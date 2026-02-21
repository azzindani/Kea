
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
import pandas as pd

logger = get_logger(__name__)

async def get_indicator_data(arguments: dict, indicator_code: str = None) -> ToolResult:
    """
    Get World Bank data for specific indicator(s).
    Args:
        economies: List of ISO3 codes (e.g. ['USA', 'CHN']). Default: All countries (if None) or Top 50.
        time_period: 'mrv' (Most Recent Value) or specific years. 
                   Default uses mrv=5 to show recent trend.
    """
    code = indicator_code or arguments.get("indicator_code")
    if not code:
        return ToolResult(isError=True, content=[TextContent(text="Indicator code required.")])
        
    economies = arguments.get("economies") # List or None for all
    mrv = arguments.get("mrv", 5)
    
    try:
        # Fetch dataframe
        # wb.data.DataFrame(series, economy, time=..., mrv=...)
        # labels=True adds Country Name column
        df = wb.data.DataFrame(code, economy=economies, mrv=mrv, labels=True)
        
        if df is None or df.empty:
            return ToolResult(content=[TextContent(text="No data found.")])
            
        return ToolResult(content=[TextContent(text=f"### Indicator: {code} (Last {mrv} values)\n\n{df.to_markdown()}")])
        
    except Exception as e:
        logger.error(f"WBGAPI error {code}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# Mapping of Friendly Name -> WDI Code
INDICATORS = {
    # Growth
    "gdp": "NY.GDP.MKTP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "inflation": "FP.CPI.TOTL.ZG",
    "fdi_net_inflows": "BX.KLT.DINV.CD.WD",
    "exports_percent_gdp": "NE.EXP.GNFS.ZS",
    "imports_percent_gdp": "NE.IMP.GNFS.ZS",
    
    # Demographics
    "population": "SP.POP.TOTL",
    "population_growth": "SP.POP.GROW",
    "life_expectancy": "SP.DYN.LE00.IN",
    "fertility_rate": "SP.DYN.TFRT.IN",
    "literacy_rate": "SE.ADT.LITR.ZS",
    "unemployment_rate": "SL.UEM.TOTL.ZS",
    "poverty_headcount": "SI.POV.DDAY",
    "gini_index": "SI.POV.GINI",
    
    # Environment
    "co2_emissions": "EN.ATM.CO2E.KT",
    "co2_per_capita": "EN.ATM.CO2E.PC",
    "forest_area": "AG.LND.FRST.ZS",
    "renewable_energy": "EG.FEC.RNEW.ZS",
    "electricity_access": "EG.ELC.ACCS.ZS",
    
    # Health/Edu
    "hospital_beds": "SH.MED.BEDS.ZS",
    "infant_mortality": "SP.DYN.IMRT.IN",
    "health_expenditure": "SH.XPD.CHEX.GD.ZS",
    
    # Tech
    "internet_usage": "IT.NET.USER.ZS",
    "mobile_subscriptions": "IT.CEL.SETS.P2",
    "high_tech_exports": "TX.VAL.TECH.MF.ZS",
    
    # Agriculture & Rural
    "arable_land": "AG.LND.ARBL.ZS",
    "agriculture_value_added": "NV.AGR.TOTL.ZS",
    "food_production_index": "AG.PRD.FOOD.XD",
    "cereal_yield": "AG.YLD.CREL.KG",
    "rural_population": "SP.RUR.TOTL.ZS",
    
    # Gender & Social
    "female_labor_participation": "SL.TLF.CACT.FE.ZS",
    "parliament_seats_women": "SG.GEN.PARL.ZS",
    "school_enrollment_primary": "SE.PRM.ENRR",
    "school_enrollment_secondary": "SE.SEC.ENRR",
    
    # Trade & Tourism
    "trade_percent_gdp": "NE.TRD.GNFS.ZS",
    "tourism_arrivals": "ST.INT.ARVL",
    "tourism_receipts": "ST.INT.RCPT.CD",
    
    # Financial
    "domestic_credit_private": "FS.AST.PRVT.GD.ZS",
    "lending_interest_rate": "FR.INR.LEND",
    "personal_remittances": "BX.TRF.PWKR.DT.GD.ZS",
    
    # Environment Extended
    "protected_areas": "ER.LND.PTLD.ZS",
    "pm25_pollution": "EN.ATM.PM25.MC.M3",
    "methane_emissions": "EN.ATM.METH.KT.CE",
    
    # Aggregates
    "total_reserves": "FI.RES.TOTL.CD",
    "military_expenditure": "MS.MIL.XPND.GD.ZS"
}

def get_indicator_map():
    return INDICATORS
