# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "pandas_ta",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    bulk, universal, signals, performance, cycles, backtest, alpha, ml, spectral,
    momentum, trend, volatility_volume, candles
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("pandas_ta_server", dependencies=["pandas", "pandas_ta"])

# --- 1. BULK / SUITE TOOLS ---
@mcp.tool()
async def get_all_indicators(data: list[dict]) -> str:
    """BULK: Calculate 100+ Indicators (All Strategies)."""
    return await bulk.get_all_indicators(data)

@mcp.tool()
async def get_momentum_suite(data: list[dict]) -> str:
    """BULK: All Momentum Indicators."""
    return await bulk.get_momentum_suite(data)

@mcp.tool()
async def get_trend_suite(data: list[dict]) -> str:
    """BULK: All Trend Indicators."""
    return await bulk.get_trend_suite(data)

@mcp.tool()
async def get_volatility_suite(data: list[dict]) -> str:
    """BULK: All Volatility Indicators."""
    return await bulk.get_volatility_suite(data)

@mcp.tool()
async def get_volume_suite(data: list[dict]) -> str:
    """BULK: All Volume Indicators."""
    return await bulk.get_volume_suite(data)

@mcp.tool()
async def get_candle_patterns_suite(data: list[dict]) -> str:
    """BULK: All Candle Patterns (60+)."""
    return await bulk.get_candle_patterns_suite(data)

@mcp.tool()
async def get_statistics_suite(data: list[dict]) -> str:
    """BULK: All Statistics (Z-Score, Skew)."""
    return await bulk.get_statistics_suite(data)

# --- 2. UNIVERSAL & SIGNALS ---
@mcp.tool()
async def calculate_any_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """UNIVERSAL: Calculate Any Indicator by Name (e.g. 'rsi')."""
    return await universal.calculate_indicator(data, indicator, params)

@mcp.tool()
async def generate_signals_from_logic(data: list[dict], condition: str) -> str:
    """LOGIC: Query Data (e.g. 'RSI_14 < 30')."""
    return await signals.generate_signals(data, condition)

# --- 3. SPECIFIC SHORTCUTS (MOMENTUM) ---
@mcp.tool()
async def calculate_rsi(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: RSI."""
    return await momentum.calculate_rsi(data, params)

@mcp.tool()
async def calculate_macd(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: MACD."""
    return await momentum.calculate_macd(data, params)

@mcp.tool()
async def calculate_stoch(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Stochastic."""
    return await momentum.calculate_stoch(data, params)

@mcp.tool()
async def calculate_cci(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: CCI."""
    return await momentum.calculate_cci(data, params)

# --- 4. SPECIFIC SHORTCUTS (TREND) ---
@mcp.tool()
async def calculate_sma(data: list[dict], params: dict = None) -> str:
    """TREND: SMA."""
    return await trend.calculate_sma(data, params)

@mcp.tool()
async def calculate_ema(data: list[dict], params: dict = None) -> str:
    """TREND: EMA."""
    return await trend.calculate_ema(data, params)

@mcp.tool()
async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """TREND: ADX."""
    return await trend.calculate_adx(data, params)

@mcp.tool()
async def calculate_supertrend(data: list[dict], params: dict = None) -> str:
    """TREND: Supertrend."""
    return await trend.calculate_supertrend(data, params)

@mcp.tool()
async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """TREND: Ichimoku Cloud."""
    return await trend.calculate_ichimoku(data, params)

# --- 5. SPECIFIC SHORTCUTS (VOLATILITY / VOLUME) ---
@mcp.tool()
async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Bollinger Bands."""
    return await volatility_volume.calculate_bbands(data, params)

@mcp.tool()
async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: ATR."""
    return await volatility_volume.calculate_atr(data, params)

@mcp.tool()
async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """VOLUME: On Balance Volume."""
    return await volatility_volume.calculate_obv(data, params)

@mcp.tool()
async def calculate_vwap(data: list[dict], params: dict = None) -> str:
    """VOLUME: VWAP."""
    return await volatility_volume.calculate_vwap(data, params)

# --- 6. ADVANCED & ML ---
@mcp.tool()
async def simple_backtest_strategy(data: list[dict], entry_signal: str, exit_signal: str) -> str:
    """BACKTEST: Run Strategy."""
    return await backtest.simple_backtest(data, entry_signal, exit_signal)

@mcp.tool()
async def construct_ml_features(data: list[dict], lags: list[int] = [1, 2, 3, 5]) -> str:
    """ML: Create Features & Targets."""
    return await ml.construct_ml_dataset(data, lags)

@mcp.tool()
async def calculate_choppiness_index(data: list[dict], params: dict = None) -> str:
    """TREND: Choppiness Index (Filter)."""
    # Using the signals alias
    return await signals.calculate_tsignals(data, params)

if __name__ == "__main__":
    mcp.run()
