
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "finta",
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.finta_server.tools import (
    bulk, universal, momentum, trend, volatility, volume, 
    exotics, levels, pressure, clouds, advanced_oscillators, 
    volume_flow, weighted, zones, exits_math
)
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("finta_server", dependencies=["pandas", "finta"])

# --- 1. BULK / SUITE TOOLS ---
# --- 1. BULK / SUITE TOOLS ---
@mcp.tool()
async def get_all_indicators(data: list[dict]) -> str:
    """CALCULATES all indicators. [ACTION]
    
    [RAG Context]
    Runs 80+ technical analysis indicators.
    Returns JSON string of results.
    """
    return await bulk.get_all_indicators(data)

@mcp.tool()
async def get_momentum_suite(data: list[dict]) -> str:
    """CALCULATES momentum suite. [ACTION]
    
    [RAG Context]
    Runs all Momentum indicators.
    Returns JSON string of results.
    """
    return await bulk.get_momentum_suite(data)

@mcp.tool()
async def get_trend_suite(data: list[dict]) -> str:
    """CALCULATES trend suite. [ACTION]
    
    [RAG Context]
    Runs all Trend indicators.
    Returns JSON string of results.
    """
    return await bulk.get_trend_suite(data)

@mcp.tool()
async def get_volatility_suite(data: list[dict]) -> str:
    """CALCULATES volatility suite. [ACTION]
    
    [RAG Context]
    Runs all Volatility indicators.
    Returns JSON string of results.
    """
    return await bulk.get_volatility_suite(data)

@mcp.tool()
async def get_volume_suite(data: list[dict]) -> str:
    """CALCULATES volume suite. [ACTION]
    
    [RAG Context]
    Runs all Volume indicators.
    Returns JSON string of results.
    """
    return await bulk.get_volume_suite(data)

# --- 2. UNIVERSAL ---
@mcp.tool()
async def calculate_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """CALCULATES specific indicator. [ACTION]
    
    [RAG Context]
    Calculates any supported indicator by name (e.g. 'RSI', 'SMA').
    Returns JSON string of results.
    """
    return await universal.calculate_indicator(data, indicator, params)

# --- 3. MOMENTUM SHORTCUTS ---
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

# ... (We can expose all shortcuts if desired, but Universal covers everything)
# Let's verify instructions: "Refactor ... remaining finance servers -> FastMCP".
# I should expose the tools listed in the original server.py to maintain parity.

@mcp.tool()
async def calculate_tsi(data: list[dict], params: dict = None) -> str:
    """CALCULATES TSI. [ACTION]
    
    [RAG Context]
    True Strength Index.
    Returns JSON string of results.
    """
    return await momentum.calculate_tsi(data, params)

@mcp.tool()
async def calculate_uo(data: list[dict], params: dict = None) -> str:
    """CALCULATES Ultimate Oscillator. [ACTION]
    
    [RAG Context]
    Ultimate Oscillator.
    Returns JSON string of results.
    """
    return await momentum.calculate_uo(data, params)

@mcp.tool()
async def calculate_roc(data: list[dict], params: dict = None) -> str:
    """CALCULATES ROC. [ACTION]
    
    [RAG Context]
    Rate of Change.
    Returns JSON string of results.
    """
    return await momentum.calculate_roc(data, params)

@mcp.tool()
async def calculate_mom(data: list[dict], params: dict = None) -> str:
    """CALCULATES Momentum. [ACTION]
    
    [RAG Context]
    Momentum indicator.
    Returns JSON string of results.
    """
    return await momentum.calculate_mom(data, params)

@mcp.tool()
async def calculate_ao(data: list[dict], params: dict = None) -> str:
    """CALCULATES AO. [ACTION]
    
    [RAG Context]
    Awesome Oscillator.
    Returns JSON string of results.
    """
    return await momentum.calculate_ao(data, params)

@mcp.tool()
async def calculate_williams(data: list[dict], params: dict = None) -> str:
    """CALCULATES Williams %R. [ACTION]
    
    [RAG Context]
    Williams %R.
    Returns JSON string of results.
    """
    return await momentum.calculate_williams(data, params)

@mcp.tool()
async def calculate_cmo(data: list[dict], params: dict = None) -> str:
    """CALCULATES CMO. [ACTION]
    
    [RAG Context]
    Chande Momentum Oscillator.
    Returns JSON string of results.
    """
    return await momentum.calculate_cmo(data, params)

@mcp.tool()
async def calculate_coppock(data: list[dict], params: dict = None) -> str:
    """CALCULATES Coppock Curve. [ACTION]
    
    [RAG Context]
    Coppock Curve.
    Returns JSON string of results.
    """
    return await momentum.calculate_coppock(data, params)

@mcp.tool()
async def calculate_fish(data: list[dict], params: dict = None) -> str:
    """CALCULATES Fisher Transform. [ACTION]
    
    [RAG Context]
    Fisher Transform.
    Returns JSON string of results.
    """
    return await momentum.calculate_fish(data, params)

@mcp.tool()
async def calculate_kama(data: list[dict], params: dict = None) -> str:
    """CALCULATES KAMA. [ACTION]
    
    [RAG Context]
    Kaufman's Adaptive Moving Average.
    Returns JSON string of results.
    """
    return await momentum.calculate_kama(data, params)

@mcp.tool()
async def calculate_vortex(data: list[dict], params: dict = None) -> str:
    """CALCULATES Vortex. [ACTION]
    
    [RAG Context]
    Vortex Indicator.
    Returns JSON string of results.
    """
    return await momentum.calculate_vortex(data, params)

@mcp.tool()
async def calculate_kst(data: list[dict], params: dict = None) -> str:
    """CALCULATES KST. [ACTION]
    
    [RAG Context]
    Know Sure Thing.
    Returns JSON string of results.
    """
    return await momentum.calculate_kst(data, params)

# --- 4. TREND SHORTCUTS ---
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
async def calculate_dema(data: list[dict], params: dict = None) -> str:
    """CALCULATES DEMA. [ACTION]
    
    [RAG Context]
    Double Exponential Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_dema(data, params)

@mcp.tool()
async def calculate_tema(data: list[dict], params: dict = None) -> str:
    """CALCULATES TEMA. [ACTION]
    
    [RAG Context]
    Triple Exponential Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_tema(data, params)

@mcp.tool()
async def calculate_trima(data: list[dict], params: dict = None) -> str:
    """CALCULATES TRIMA. [ACTION]
    
    [RAG Context]
    Triangular Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_trima(data, params)

@mcp.tool()
async def calculate_wma(data: list[dict], params: dict = None) -> str:
    """CALCULATES WMA. [ACTION]
    
    [RAG Context]
    Weighted Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_wma(data, params)

@mcp.tool()
async def calculate_hma(data: list[dict], params: dict = None) -> str:
    """CALCULATES HMA. [ACTION]
    
    [RAG Context]
    Hull Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_hma(data, params)

@mcp.tool()
async def calculate_zlema(data: list[dict], params: dict = None) -> str:
    """CALCULATES ZLEMA. [ACTION]
    
    [RAG Context]
    Zero Lag Exponential Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_zlema(data, params)

@mcp.tool()
async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """CALCULATES ADX. [ACTION]
    
    [RAG Context]
    Average Directional Index.
    Returns JSON string of results.
    """
    return await trend.calculate_adx(data, params)

@mcp.tool()
async def calculate_ssma(data: list[dict], params: dict = None) -> str:
    """CALCULATES SSMA. [ACTION]
    
    [RAG Context]
    Smoothed Simple Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_ssma(data, params)

@mcp.tool()
async def calculate_smma(data: list[dict], params: dict = None) -> str:
    """CALCULATES SMMA. [ACTION]
    
    [RAG Context]
    Smoothed Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_smma(data, params)

@mcp.tool()
async def calculate_frama(data: list[dict], params: dict = None) -> str:
    """CALCULATES FRAMA. [ACTION]
    
    [RAG Context]
    Fractal Adaptive Moving Average.
    Returns JSON string of results.
    """
    return await trend.calculate_frama(data, params)

@mcp.tool()
async def calculate_sar(data: list[dict], params: dict = None) -> str:
    """CALCULATES SAR. [ACTION]
    
    [RAG Context]
    Parabolic SAR (Stop and Reverse).
    Returns JSON string of results.
    """
    return await trend.calculate_sar(data, params)

# --- 5. VOLATILITY ---
@mcp.tool()
async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """CALCULATES ATR. [ACTION]
    
    [RAG Context]
    Average True Range.
    Returns JSON string of results.
    """
    return await volatility.calculate_atr(data, params)

@mcp.tool()
async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """CALCULATES Bollinger Bands. [ACTION]
    
    [RAG Context]
    Bollinger Bands (Upper, Middle, Lower).
    Returns JSON string of results.
    """
    return await volatility.calculate_bbands(data, params)

@mcp.tool()
async def calculate_kc(data: list[dict], params: dict = None) -> str:
    """CALCULATES Keltner Channels. [ACTION]
    
    [RAG Context]
    Keltner Channels.
    Returns JSON string of results.
    """
    return await volatility.calculate_kc(data, params)

@mcp.tool()
async def calculate_do(data: list[dict], params: dict = None) -> str:
    """CALCULATES Donchian Channels. [ACTION]
    
    [RAG Context]
    Donchian Channels.
    Returns JSON string of results.
    """
    return await volatility.calculate_do(data, params)

@mcp.tool()
async def calculate_mobo(data: list[dict], params: dict = None) -> str:
    """CALCULATES MOBO Bands. [ACTION]
    
    [RAG Context]
    Momentum Breakout Bands.
    Returns JSON string of results.
    """
    return await volatility.calculate_mobo(data, params)

@mcp.tool()
async def calculate_tr(data: list[dict], params: dict = None) -> str:
    """CALCULATES True Range. [ACTION]
    
    [RAG Context]
    True Range.
    Returns JSON string of results.
    """
    return await volatility.calculate_tr(data, params)

@mcp.tool()
async def calculate_bbwidth(data: list[dict], params: dict = None) -> str:
    """CALCULATES BB Width. [ACTION]
    
    [RAG Context]
    Bollinger Band Width.
    Returns JSON string of results.
    """
    return await volatility.calculate_bbwidth(data, params)

@mcp.tool()
async def calculate_percent_b(data: list[dict], params: dict = None) -> str:
    """CALCULATES Percent B. [ACTION]
    
    [RAG Context]
    Bollinger %B.
    Returns JSON string of results.
    """
    return await volatility.calculate_percent_b(data, params)

@mcp.tool()
async def calculate_apz(data: list[dict], params: dict = None) -> str:
    """CALCULATES APZ. [ACTION]
    
    [RAG Context]
    Adaptive Price Zone.
    Returns JSON string of results.
    """
    return await volatility.calculate_apz(data, params)

@mcp.tool()
async def calculate_massi(data: list[dict], params: dict = None) -> str:
    """CALCULATES Mass Index. [ACTION]
    
    [RAG Context]
    Mass Index.
    Returns JSON string of results.
    """
    return await volatility.calculate_massi(data, params)

# --- 6. VOLUME ---
@mcp.tool()
async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """CALCULATES OBV. [ACTION]
    
    [RAG Context]
    On-Balance Volume.
    Returns JSON string of results.
    """
    return await volume.calculate_obv(data, params)

@mcp.tool()
async def calculate_mfi(data: list[dict], params: dict = None) -> str:
    """CALCULATES MFI. [ACTION]
    
    [RAG Context]
    Money Flow Index.
    Returns JSON string of results.
    """
    return await volume.calculate_mfi(data, params)

@mcp.tool()
async def calculate_adl(data: list[dict], params: dict = None) -> str:
    """CALCULATES ADL. [ACTION]
    
    [RAG Context]
    Accumulation/Distribution Line.
    Returns JSON string of results.
    """
    return await volume.calculate_adl(data, params)

@mcp.tool()
async def calculate_chaikin(data: list[dict], params: dict = None) -> str:
    """CALCULATES Chaikin Osc. [ACTION]
    
    [RAG Context]
    Chaikin Oscillator.
    Returns JSON string of results.
    """
    return await volume.calculate_chaikin(data, params)

@mcp.tool()
async def calculate_efi(data: list[dict], params: dict = None) -> str:
    """CALCULATES Force Index. [ACTION]
    
    [RAG Context]
    Elder's Force Index.
    Returns JSON string of results.
    """
    return await volume.calculate_efi(data, params)

@mcp.tool()
async def calculate_vpt(data: list[dict], params: dict = None) -> str:
    """CALCULATES VPT. [ACTION]
    
    [RAG Context]
    Volume Price Trend.
    Returns JSON string of results.
    """
    return await volume.calculate_vpt(data, params)

@mcp.tool()
async def calculate_emv(data: list[dict], params: dict = None) -> str:
    """CALCULATES EMV. [ACTION]
    
    [RAG Context]
    Ease of Movement.
    Returns JSON string of results.
    """
    return await volume.calculate_emv(data, params)

@mcp.tool()
async def calculate_nvi(data: list[dict], params: dict = None) -> str:
    """CALCULATES NVI. [ACTION]
    
    [RAG Context]
    Negative Volume Index.
    Returns JSON string of results.
    """
    return await volume.calculate_nvi(data, params)

@mcp.tool()
async def calculate_pvi(data: list[dict], params: dict = None) -> str:
    """CALCULATES PVI. [ACTION]
    
    [RAG Context]
    Positive Volume Index.
    Returns JSON string of results.
    """
    return await volume.calculate_pvi(data, params)

@mcp.tool()
async def calculate_vzo(data: list[dict], params: dict = None) -> str:
    """CALCULATES VZO. [ACTION]
    
    [RAG Context]
    Volume Zone Oscillator.
    Returns JSON string of results.
    """
    return await volume.calculate_vzo(data, params)

# --- 7. EXOTICS & LEVELS ---
@mcp.tool()
async def calculate_wto(data: list[dict], params: dict = None) -> str:
    """CALCULATES Wave Trend. [ACTION]
    
    [RAG Context]
    Wave Trend Oscillator.
    Returns JSON string of results.
    """
    return await exotics.calculate_wto(data, params)

@mcp.tool()
async def calculate_stc(data: list[dict], params: dict = None) -> str:
    """CALCULATES STC. [ACTION]
    
    [RAG Context]
    Schaff Trend Cycle.
    Returns JSON string of results.
    """
    return await exotics.calculate_stc(data, params)

@mcp.tool()
async def calculate_ev_macd(data: list[dict], params: dict = None) -> str:
    """CALCULATES EV MACD. [ACTION]
    
    [RAG Context]
    Elastic Volume MACD.
    Returns JSON string of results.
    """
    return await exotics.calculate_ev_macd(data, params)

@mcp.tool()
async def calculate_alma(data: list[dict], params: dict = None) -> str:
    """CALCULATES ALMA. [ACTION]
    
    [RAG Context]
    Arnaud Legoux Moving Average.
    Returns JSON string of results.
    """
    return await exotics.calculate_alma(data, params)

@mcp.tool()
async def calculate_vama(data: list[dict], params: dict = None) -> str:
    """CALCULATES VAMA. [ACTION]
    
    [RAG Context]
    Volume Adjusted Moving Average.
    Returns JSON string of results.
    """
    return await exotics.calculate_vama(data, params)

@mcp.tool()
async def calculate_pivot(data: list[dict], params: dict = None) -> str:
    """CALCULATES Pivot Points. [ACTION]
    
    [RAG Context]
    Standard Pivot Points.
    Returns JSON string of results.
    """
    return await levels.calculate_pivot(data, params)

@mcp.tool()
async def calculate_fib_pivot(data: list[dict], params: dict = None) -> str:
    """CALCULATES Fibonacci Pivots. [ACTION]
    
    [RAG Context]
    Fibonacci Pivot Points.
    Returns JSON string of results.
    """
    return await levels.calculate_fib_pivot(data, params)

@mcp.tool()
async def calculate_basp(data: list[dict], params: dict = None) -> str:
    """CALCULATES Buy/Sell Pressure. [ACTION]
    
    [RAG Context]
    Buy vs Sell Pressure.
    Returns JSON string of results.
    """
    return await pressure.calculate_basp(data, params)

@mcp.tool()
async def calculate_ebbp(data: list[dict], params: dict = None) -> str:
    """CALCULATES Bull/Bear Power. [ACTION]
    
    [RAG Context]
    Elder Ray Index (Bull/Bear Power).
    Returns JSON string of results.
    """
    return await pressure.calculate_ebbp(data, params)

# --- 8. PHASES 3 & 4 (Clouds, Flow, Weighted, etc) ---
@mcp.tool()
async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """CALCULATES Ichimoku. [ACTION]
    
    [RAG Context]
    Ichimoku Cloud.
    Returns JSON string of results.
    """
    return await clouds.calculate_ichimoku(data, params)

@mcp.tool()
async def calculate_trix(data: list[dict], params: dict = None) -> str:
    """CALCULATES TRIX. [ACTION]
    
    [RAG Context]
    Triple Exponential Average.
    Returns JSON string of results.
    """
    return await advanced_oscillators.calculate_trix(data, params)

@mcp.tool()
async def calculate_ift_rsi(data: list[dict], params: dict = None) -> str:
    """CALCULATES IFT RSI. [ACTION]
    
    [RAG Context]
    Inverse Fisher Transform RSI.
    Returns JSON string of results.
    """
    return await advanced_oscillators.calculate_ift_rsi(data, params)

@mcp.tool()
async def calculate_sqzmi(data: list[dict], params: dict = None) -> str:
    """CALCULATES Squeeze Momentum. [ACTION]
    
    [RAG Context]
    Squeeze Momentum Indicator.
    Returns JSON string of results.
    """
    return await advanced_oscillators.calculate_sqzmi(data, params)

@mcp.tool()
async def calculate_vfi(data: list[dict], params: dict = None) -> str:
    """CALCULATES Volume Flow. [ACTION]
    
    [RAG Context]
    Volume Flow Indicator.
    Returns JSON string of results.
    """
    return await volume_flow.calculate_vfi(data, params)

@mcp.tool()
async def calculate_fve(data: list[dict], params: dict = None) -> str:
    """CALCULATES FVE. [ACTION]
    
    [RAG Context]
    Finite Volume Element.
    Returns JSON string of results.
    """
    return await volume_flow.calculate_fve(data, params)

@mcp.tool()
async def calculate_qstick(data: list[dict], params: dict = None) -> str:
    """CALCULATES QStick. [ACTION]
    
    [RAG Context]
    QStick Indicator.
    Returns JSON string of results.
    """
    return await volume_flow.calculate_qstick(data, params)

@mcp.tool()
async def calculate_msd(data: list[dict], params: dict = None) -> str:
    """CALCULATES Moving Std Dev. [ACTION]
    
    [RAG Context]
    Moving Standard Deviation.
    Returns JSON string of results.
    """
    return await volume_flow.calculate_msd(data, params)

@mcp.tool()
async def calculate_vwap_finta(data: list[dict], params: dict = None) -> str:
    """CALCULATES VWAP. [ACTION]
    
    [RAG Context]
    Volume Weighted Average Price.
    Returns JSON string of results.
    """
    return await weighted.calculate_vwap(data, params)

@mcp.tool()
async def calculate_evwma(data: list[dict], params: dict = None) -> str:
    """CALCULATES EVWMA. [ACTION]
    
    [RAG Context]
    Elastic Volume Weighted Moving Average.
    Returns JSON string of results.
    """
    return await weighted.calculate_evwma(data, params)

@mcp.tool()
async def calculate_wobv(data: list[dict], params: dict = None) -> str:
    """CALCULATES Weighted OBV. [ACTION]
    
    [RAG Context]
    Weighted On-Balance Volume.
    Returns JSON string of results.
    """
    return await weighted.calculate_wobv(data, params)

@mcp.tool()
async def calculate_pzo(data: list[dict], params: dict = None) -> str:
    """CALCULATES Price Zone Osc. [ACTION]
    
    [RAG Context]
    Price Zone Oscillator.
    Returns JSON string of results.
    """
    return await zones.calculate_pzo(data, params)

@mcp.tool()
async def calculate_cfi(data: list[dict], params: dict = None) -> str:
    """CALCULATES Cumulative Force. [ACTION]
    
    [RAG Context]
    Cumulative Force Index.
    Returns JSON string of results.
    """
    return await zones.calculate_cfi(data, params)

@mcp.tool()
async def calculate_tp(data: list[dict], params: dict = None) -> str:
    """CALCULATES Typical Price. [ACTION]
    
    [RAG Context]
    Typical Price.
    Returns JSON string of results.
    """
    return await zones.calculate_tp(data, params)

@mcp.tool()
async def calculate_chandelier(data: list[dict], params: dict = None) -> str:
    """CALCULATES Chandelier. [ACTION]
    
    [RAG Context]
    Chandelier Exit.
    Returns JSON string of results.
    """
    return await exits_math.calculate_chandelier(data, params)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class FintaServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
