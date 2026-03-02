
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "pandas_ta",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.pandas_ta_server.tools import (
    bulk, universal, signals, performance, cycles, backtest, alpha, ml, spectral,
    momentum, trend, volatility_volume, candles
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("pandas_ta_server", dependencies=["pandas", "pandas_ta"])

# --- 1. BULK / SUITE TOOLS ---
@mcp.tool()
async def get_all_indicators(data: list[dict]) -> str:
    """CALCULATES all indicators. [ACTION]
    
    [RAG Context]
    A heavy-duty quantitative analysis tool that executes the entire pandas-ta library (130+ indicators) on a single dataset.
    
    How to Use:
    - Input 'data' must be an OHLCV list of dicts.
    - Performance Warning: This is resource-intensive. For specific needs, use 'calculate_any_indicator' or themed suites.
    
    Keywords: quantitative suite, indicator batch, alpha generation, feature engineering.
    """
    return await bulk.get_all_indicators(data)

@mcp.tool()
async def get_momentum_suite(data: list[dict]) -> str:
    """CALCULATES momentum suite. [ACTION]
    
    [RAG Context]
    A robust "Super Tool" for analyzing price velocity and strength. It runs a batch of indicators including RSI, MACD, AO, BOP, and Stochastic in a single high-performance operation.
    
    How to Use:
    - Best for identifying overextended markets where a reversal is imminent.
    - Input OHLCV data.
    
    Keywords: momentum analysis, price velocity, trade strength, divergence suite.
    """
    return await bulk.get_momentum_suite(data)

@mcp.tool()
async def get_trend_suite(data: list[dict]) -> str:
    """CALCULATES trend suite. [ACTION]
    
    [RAG Context]
    A comprehensive "Super Tool" for structural market analysis. It calculates the prevailing direction and strength of the price movement using SMAs, EMAs, ADX, and Supertrend.
    
    How to Use:
    - Essential for determining if a market is in a sustained Bull or Bear run.
    - Used to filter out entries that go against the primary market flow.
    
    Keywords: trend recognition, moving average batch, market flow, structural analysis.
    """
    return await bulk.get_trend_suite(data)

@mcp.tool()
async def get_volatility_suite(data: list[dict]) -> str:
    """CALCULATES volatility suite. [ACTION]
    
    [RAG Context]
    Runs all Volatility indicators (BBands, ATR, etc).
    Returns JSON string of results.
    """
    return await bulk.get_volatility_suite(data)

@mcp.tool()
async def get_volume_suite(data: list[dict]) -> str:
    """CALCULATES volume suite. [ACTION]
    
    [RAG Context]
    Runs all Volume indicators (OBV, VWAP, etc).
    Returns JSON string of results.
    """
    return await bulk.get_volume_suite(data)

@mcp.tool()
async def get_candle_patterns_suite(data: list[dict]) -> str:
    """IDENTIFIES candle patterns. [ACTION]
    
    [RAG Context]
    A specialized pattern recognition engine that identifies 60+ distinct Japanese Candlestick formations.
    
    How to Use:
    - Patterns include: Doji, Hammer, Shooting Star, Morning Star, Three White Soldiers, etc.
    - Returns a boolean structure indicating where patterns were detected in the time series.
    
    Keywords: pattern recognition, candlestick signals, price action, chart patterns.
    """
    return await bulk.get_candle_patterns_suite(data)

@mcp.tool()
async def get_statistics_suite(data: list[dict]) -> str:
    """CALCULATES statistics suite. [ACTION]
    
    [RAG Context]
    Runs statistical analysis (Z-Score, Skew, Kurtosis).
    Returns JSON string of results.
    """
    return await bulk.get_statistics_suite(data)

# --- 2. UNIVERSAL & SIGNALS ---
@mcp.tool()
async def calculate_any_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """CALCULATES specific indicator. [ACTION]
    
    [RAG Context]
    The primary entry point for granular analysis. Allows calling any individual pandas-ta indicator by its abbreviated string name (e.g., 'rsi', 'macd', 'stoch', 'cci').
    
    Keywords: technical study, indicator factory, custom analysis, alpha factor.
    """
    return await universal.calculate_indicator(data, indicator, params)

@mcp.tool()
async def generate_signals_from_logic(data: list[dict], condition: str) -> str:
    """GENERATES trading signals. [ACTION]
    
    [RAG Context]
    An intelligent "Super Tool" that translates human-readable trading rules into actionable Buy/Sell events. It evaluates any custom logical expression against the time-series data.
    
    How to Use:
    - 'condition': A string expression using indicator names (e.g., 'RSI_14 < 30 and CLOSE > EMA_200').
    - Returns a list of timestamps and signal values (+1 for Buy, -1 for Sell).
    
    Keywords: algorithmic signal, rule engine, trade triggers, logic evaluator.
    """
    return await signals.generate_signals(data, condition)

# --- 3. SPECIFIC SHORTCUTS (MOMENTUM) ---
@mcp.tool()
async def calculate_rsi(data: list[dict], params: dict = None) -> str:
    """CALCULATES RSI. [ACTION]
    
    [RAG Context]
    Relative Strength Index.
    Returns JSON string of results.
    """
    return await momentum.calculate_rsi(data, params)

@mcp.tool()
async def calculate_macd(data: list[dict], params: dict = None) -> str:
    """CALCULATES MACD. [ACTION]
    
    [RAG Context]
    Moving Average Convergence Divergence.
    Returns JSON string of results.
    """
    return await momentum.calculate_macd(data, params)

@mcp.tool()
async def calculate_stoch(data: list[dict], params: dict = None) -> str:
    """CALCULATES Stochastic. [ACTION]
    
    [RAG Context]
    Stochastic Oscillator.
    Returns JSON string of results.
    """
    return await momentum.calculate_stoch(data, params)

@mcp.tool()
async def calculate_cci(data: list[dict], params: dict = None) -> str:
    """CALCULATES CCI. [ACTION]
    
    [RAG Context]
    Commodity Channel Index.
    Returns JSON string of results.
    """
    return await momentum.calculate_cci(data, params)

# --- 4. SPECIFIC SHORTCUTS (TREND) ---
@mcp.tool()
async def calculate_sma(data: list[dict], params: dict = None) -> str:
    """CALCULATES SMA. [ACTION]
    
    [RAG Context]
    Simple Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_sma(data, params)

@mcp.tool()
async def calculate_ema(data: list[dict], params: dict = None) -> str:
    """CALCULATES EMA. [ACTION]
    
    [RAG Context]
    Exponential Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_ema(data, params)

@mcp.tool()
async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """CALCULATES ADX. [ACTION]
    
    [RAG Context]
    Average Directional Index (Trend Strength).
    Returns JSON string of results.
    """
    return await trend.calculate_adx(data, params)

@mcp.tool()
async def calculate_supertrend(data: list[dict], params: dict = None) -> str:
    """CALCULATES Supertrend. [ACTION]
    
    [RAG Context]
    A versatile "Super Tool" for trend following. It uses ATR-based volatility channels to define support and resistance levels that trail the price action.
    
    How to Use:
    - Returns the trend direction (up/down) and the current stop-loss level.
    - Widely used by retail and institutional traders for robust trend captures.
    
    Keywords: automated trend, volatility trail, trend switch, dynamic support.
    """
    return await trend.calculate_supertrend(data, params)

@mcp.tool()
async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """CALCULATES Ichimoku. [ACTION]
    
    [RAG Context]
    Ichimoku Cloud components.
    Returns JSON string of results.
    """
    return await trend.calculate_ichimoku(data, params)

# --- 5. SPECIFIC SHORTCUTS (VOLATILITY / VOLUME) ---
@mcp.tool()
async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """CALCULATES Bollinger Bands. [ACTION]
    
    [RAG Context]
    Volatility bands (Upper, Middle, Lower).
    Returns JSON string of results.
    """
    return await volatility_volume.calculate_bbands(data, params)

@mcp.tool()
async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """CALCULATES ATR. [ACTION]
    
    [RAG Context]
    Average True Range (Volatility).
    Returns JSON string of results.
    """
    return await volatility_volume.calculate_atr(data, params)

@mcp.tool()
async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """CALCULATES OBV. [ACTION]
    
    [RAG Context]
    On-Balance Volume.
    Returns JSON string of results.
    """
    return await volatility_volume.calculate_obv(data, params)

@mcp.tool()
async def calculate_vwap(data: list[dict], params: dict = None) -> str:
    """CALCULATES VWAP. [ACTION]
    
    [RAG Context]
    Volume Weighted Average Price.
    Returns JSON string of results.
    """
    return await volatility_volume.calculate_vwap(data, params)

# --- 6. ADVANCED & ML ---
@mcp.tool()
async def simple_backtest_strategy(data: list[dict], entry_signal: str, exit_signal: str) -> str:
    """RUNS backtest. [ACTION]
    
    [RAG Context]
    Simulates a historical trading strategy by mapping entry and exit conditions onto the provided dataset. 
    
    How to Use:
    - Returns summary metrics: Win Rate, Total Return, Max Drawdown, and Sharpe Ratio.
    - Essential for validating a hypothesis before going live.
    
    Keywords: strategy testing, performance audit, win rate, historical simulation.
    """
    return await backtest.simple_backtest(data, entry_signal, exit_signal)

@mcp.tool()
async def construct_ml_features(data: list[dict], lags: list[int] = [1, 2, 3, 5]) -> str:
    """CONSTRUCTS ML features. [ACTION]
    
    [RAG Context]
    A pre-processing tool for machine learning. Transforms a raw time series into a supervised learning dataset by creating lagged features and a target variable.
    
    Keywords: feature engineering, dataset prep, lag variables, supervised learning.
    """
    return await ml.construct_ml_dataset(data, lags)

@mcp.tool()
async def calculate_choppiness_index(data: list[dict], params: dict = None) -> str:
    """CALCULATES Choppiness Index. [ACTION]
    
    [RAG Context]
    Determines if market is choppy (ranging) or trending.
    Returns JSON string of results.
    """
    # Using the signals alias
    return await signals.calculate_tsignals(data, params)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class PandasTaServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

