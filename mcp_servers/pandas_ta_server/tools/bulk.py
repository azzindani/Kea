
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_json
import pandas_ta as ta
import pandas as pd
from shared.logging.main import get_logger

logger = get_logger(__name__)

# Explicit Lists for Fallback
MOMENTUM_INDS = ["rsi", "macd", "stoch", "cci", "roc", "ao", "mom", "tsi", "uo", "bop", "fisher", "cg", "stochrsi", "squeeze", "rsx"]
TREND_INDS = ["sma", "ema", "wma", "hma", "adx", "vortex", "aroon", "dpo", "psar", "supertrend", "chop", "zigzag", "ttm_trend"]
VOLATILITY_INDS = ["bbands", "atr", "kc", "donchian", "accbands", "natr", "thermo", "ui", "massi", "pdist", "rvi"]
VOLUME_INDS = ["obv", "cmf", "mfi", "vwap", "adl", "pvi", "nvi", "eom"]
# Candles handled separately
STATISTICS_INDS = ["zscore", "skew", "kurtosis", "entropy", "variance", "stdev", "mad"]

async def run_indicators_manually(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Manually iterate indicators if strategy() fails."""
    inds = []
    if category == "Momentum": inds = MOMENTUM_INDS
    elif category == "Trend": inds = TREND_INDS
    elif category == "Volatility": inds = VOLATILITY_INDS
    elif category == "Volume": inds = VOLUME_INDS
    elif category == "Statistics": inds = STATISTICS_INDS
    elif category == "All": 
        inds = MOMENTUM_INDS + TREND_INDS + VOLATILITY_INDS + VOLUME_INDS + STATISTICS_INDS
    
    success_count = 0
    for ind in inds:
        try:
            if hasattr(df.ta, ind):
                method = getattr(df.ta, ind)
                # Some indicators require params, use defaults.
                # append=True adds to df
                method(append=True)
                success_count += 1
        except Exception as e:
            # ignore individual failures (e.g. need data length)
            pass
            
    # For Candles, it's a single function usually
    if category == "Candles" or category == "All":
        try:
            df.ta.cdl_pattern(name="all", append=True)
            success_count += 1
        except:
            pass
            
    return df


async def get_category_suite(data: list[dict], category: str = "Momentum") -> str:
    """
    Run a Specific Category Suite.
    Args:
        data: OHLCV List/JSON.
        category: "Momentum", "Trend", "Volatility", "Volume", "Overlap".
    """
    try:
        df = process_ohlcv(data)
        
        # Try Standard Strategy
        try:
            # Valid categories: "Candles", "Cycles", "Momentum", "Overlap", "Performance", "Statistics", "Trend", "Volatility", "Volume"
            # If category is "All", use "All"
            df.ta.strategy(category, verbose=False)
        except (AttributeError, Exception) as e:
            # Fallback
            # logger.warning(f"Strategy '{category}' failed ({e}). Running manual fallback.")
            await run_indicators_manually(df, category)
        
        return df_to_json(df, f"{category} Suite")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_all_indicators(data: list[dict]) -> str:
    """Run 'All' Strategy."""
    return await get_category_suite(data, "All")



# Wrappers (Same as before)
async def get_momentum_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Momentum")

async def get_trend_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Trend")

async def get_volatility_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Volatility")

async def get_volume_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Volume")

async def get_candle_patterns_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Candles")

async def get_statistics_suite(data: list[dict]) -> str:
    return await get_category_suite(data, "Statistics")

