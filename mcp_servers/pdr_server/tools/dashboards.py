

from shared.logging.main import get_logger
import datetime
import pandas as pd

from mcp_servers.pdr_server.tools.famafrench import read_famafrench

logger = get_logger(__name__)


async def get_factor_dashboard() -> str:
    """
    Get Academic Factors Dashboard (Market, Size, Value, Momentum).
    """
    start = datetime.datetime.now() - datetime.timedelta(days=365*2)
    
    try:
        # Fetch 5 Factors and Momentum
        # Note: pandas_datareader might allow multiple codes, but famafrench module takes ONE dataset at a time usually.
        # We must make separate calls and merge.
        
        # 1. 5 Factors
        f5 = read_famafrench("F-F_Research_Data_5_Factors_2x3_daily", start=start)
        df_f5 = f5[0] # Monthly/Daily table

        # 2. Momentum
        mom = read_famafrench("F-F_Momentum_Factor_daily", start=start)
        df_mom = mom[0]
        
        # Join
        df_all = df_f5.join(df_mom, how='inner')
        
        return f"### Academic Factors Dashboard (Daily %)\n\n{df_all.tail(30).to_markdown()}"
        
    except Exception as e:
        return f"Error: {str(e)}"

async def get_global_factors_dashboard() -> str:
    """
    Get Global Factors (Developed, Emerging, Europe, Japan).
    """
    start = datetime.datetime.now() - datetime.timedelta(days=365*2)
    datasets = {
        "Developed": "Developed_3_Factors",
        "Emerging": "Emerging_5_Factors",
        "Europe": "Europe_3_Factors",
        "Japan": "Japan_3_Factors"
    }
    
    try:
        results = {}
        for region, code in datasets.items():
            data = read_famafrench(code, start=start)
            # Take the Mkt-RF column roughly (usually first column is Mkt-RF)
            # Actually keys usually 0 is monthly.
            df = data[0]
            if not df.empty:
                # Rename 'Mkt-RF' to 'Region-Mkt'
                if 'Mkt-RF' in df.columns:
                     results[f"{region}"] = df['Mkt-RF']
        
        final_df = pd.DataFrame(results)
        return f"### Global Market Factors (Excess Returns)\n\n{final_df.tail(20).to_markdown()}"
        
    except Exception as e:
        return f"Error: {str(e)}"

async def get_industry_health_dashboard() -> str:
    """
    Get Fama-French 49 Industry Health Dashboard.
    Shows recent performance of 49 sectors.
    """
    start = datetime.datetime.now() - datetime.timedelta(days=365) # 1 Year view
    
    try:
        data = read_famafrench("49_Industry_Portfolios_daily", start=start) # Daily
        df = data[0] # Value weighted returns usually
        
        return f"### 49 Industry Health (Daily Returns %)\n\n{df.tail(10).to_markdown()}"
        
    except Exception as e:
        return f"Error: {str(e)}"

async def get_liquidity_dashboard() -> str:
    """
    Get Liquidity Factors (Pastor-Stambaugh).
    """
    start = datetime.datetime.now() - datetime.timedelta(days=365*2)
    try:
        data = read_famafrench("Liquidity_Factor", start=start)
        df = data[0]
        return f"### Market Liquidity Factor\n\n{df.tail(20).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

