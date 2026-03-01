
from mcp_servers.finta_server.tools.core import process_ohlcv, df_to_json
from finta import TA
import pandas as pd
from shared.logging.main import get_logger

logger = get_logger(__name__)

# Categorize Indicators manually based on Finta documentation/knowledge
# This helps in creating suites.
MOMENTUM_INDS = ["RSI", "MACD", "STOCH", "TSI", "UO", "ROC", "MOM", "AO", "WILLIAMS", "CMO", "COPP", "FISH", "KAMA", "VORTEX", "KST", "PPO", "STOCHRSI", "SQZMI"]
TREND_INDS = ["SMA", "EMA", "DEMA", "TEMA", "TRIMA", "WMA", "HMA", "ZLEMA", "ADX", "KAMA", "SSMA", "SMMA", "FRAMA", "SAR"]
VOLATILITY_INDS = ["ATR", "BBANDS", "KC", "DO", "MOBO", "TR", "BBWIDTH", "PERCENT_B", "APZ", "MASSI", "CHANDELIER"]
VOLUME_INDS = ["OBV", "MFI", "ADL", "CHAIKIN", "EFI", "VPT", "EMV", "NVI", "PVI", "VZO", "FVE", "VFI"]

async def run_suite(df: pd.DataFrame, inds: list) -> pd.DataFrame:
    """Run a list of indicators."""
    results = pd.DataFrame(index=df.index)
    # We want to merge results.
    # Finta returns Series or DataFrame.
    
    for ind in inds:
        try:
            if hasattr(TA, ind):
                method = getattr(TA, ind)
                res = method(df)
                
                # Check outcome type
                if isinstance(res, pd.Series):
                    res.name = ind
                    results = results.join(res, how='outer')
                elif isinstance(res, pd.DataFrame):
                    # Prefix columns? Or just join
                    # Finta DF columns are usually like 'MACD', 'SIGNAL'. 
                    # If duplicate names, might clash.
                    # Let's prefix with Indicator Name if generic.
                    res.columns = [f"{ind}_{c}" for c in res.columns]
                    results = results.join(res, how='outer')
        except Exception as e:
            # logger.warning(f"Failed {ind}: {e}")
            pass
            
    return results


async def get_all_indicators(data: list[dict]) -> str:
    """
    Run ALL available Finta indicators.
    WARNING: Heavy computation.
    """
    try:
        # data = arguments.get("data")
        df = process_ohlcv(data)
        
        # Combine all lists
        all_inds = list(set(MOMENTUM_INDS + TREND_INDS + VOLATILITY_INDS + VOLUME_INDS))
        
        res_df = await run_suite(df, all_inds)
        # Also join with original data?
        # Usually users want indicators appended.
        final_df = df.join(res_df, how='outer')
        
        return df_to_json(final_df, "All Indicators")
    except Exception as e:
        return f"Error: {str(e)}"



async def get_momentum_suite(data: list[dict]) -> str:
    """Run Momentum Suite."""
    try:
        df = process_ohlcv(data)
        res_df = await run_suite(df, MOMENTUM_INDS)
        return df_to_json(df.join(res_df, how='outer'), "Momentum Suite")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_trend_suite(data: list[dict]) -> str:
    """Run Trend Suite."""
    try:
        df = process_ohlcv(data)
        res_df = await run_suite(df, TREND_INDS)
        return df_to_json(df.join(res_df, how='outer'), "Trend Suite")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_volatility_suite(data: list[dict]) -> str:
    """Run Volatility Suite."""
    try:
        df = process_ohlcv(data)
        res_df = await run_suite(df, VOLATILITY_INDS)
        return df_to_json(df.join(res_df, how='outer'), "Volatility Suite")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_volume_suite(data: list[dict]) -> str:
    """Run Volume Suite."""
    try:
        df = process_ohlcv(data)
        res_df = await run_suite(df, VOLUME_INDS)
        return df_to_json(df.join(res_df, how='outer'), "Volume Suite")
    except Exception as e:
        return f"Error: {str(e)}"

