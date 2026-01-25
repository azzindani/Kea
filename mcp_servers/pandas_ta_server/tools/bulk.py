
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.core import process_ohlcv, df_to_result
import pandas_ta as ta
import pandas as pd
from shared.logging import get_logger

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

async def get_category_suite(arguments: dict) -> ToolResult:
    """
    Run a Specific Category Suite.
    Args:
        data: OHLCV List/JSON.
        category: "Momentum", "Trend", "Volatility", "Volume", "Overlap".
    """
    try:
        data = arguments.get("data")
        category = arguments.get("category", "Momentum")
        
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
        
        return df_to_result(df, f"{category} Suite")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_all_indicators(arguments: dict) -> ToolResult:
    """Run 'All' Strategy."""
    arguments['category'] = "All"
    return await get_category_suite(arguments)

# Wrappers (Same as before)
async def get_momentum_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Momentum"
    return await get_category_suite(arguments)

async def get_trend_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Trend"
    return await get_category_suite(arguments)

async def get_volatility_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Volatility"
    return await get_category_suite(arguments)

async def get_volume_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Volume"
    return await get_category_suite(arguments)

async def get_candle_patterns_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Candles"
    return await get_category_suite(arguments)

async def get_statistics_suite(arguments: dict) -> ToolResult:
    arguments['category'] = "Statistics"
    return await get_category_suite(arguments)
