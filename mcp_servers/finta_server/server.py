from mcp.server.fastmcp import FastMCP
from mcp_servers.finta_server.tools import (
    bulk, universal, momentum, trend, volatility, volume, 
    exotics, levels, pressure, clouds, advanced_oscillators, 
    volume_flow, weighted, zones, exits_math
)
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("finta_server", dependencies=["pandas", "finta"])

# --- 1. BULK / SUITE TOOLS ---
@mcp.tool()
async def get_all_indicators(data: list[dict]) -> str:
    """BULK: Calculate 80+ Indicators."""
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

# --- 2. UNIVERSAL ---
@mcp.tool()
async def calculate_indicator(data: list[dict], indicator: str, params: dict = None) -> str:
    """UNIVERSAL: Calculate Any Indicator (e.g. 'RSI')."""
    return await universal.calculate_indicator(data, indicator, params)

# --- 3. MOMENTUM SHORTCUTS ---
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

# ... (We can expose all shortcuts if desired, but Universal covers everything)
# Let's verify instructions: "Refactor ... remaining finance servers -> FastMCP".
# I should expose the tools listed in the original server.py to maintain parity.

@mcp.tool()
async def calculate_tsi(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: TSI."""
    return await momentum.calculate_tsi(data, params)

@mcp.tool()
async def calculate_uo(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Ultimate Oscillator."""
    return await momentum.calculate_uo(data, params)

@mcp.tool()
async def calculate_roc(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Rate of Change."""
    return await momentum.calculate_roc(data, params)

@mcp.tool()
async def calculate_mom(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Momentum."""
    return await momentum.calculate_mom(data, params)

@mcp.tool()
async def calculate_ao(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: AO."""
    return await momentum.calculate_ao(data, params)

@mcp.tool()
async def calculate_williams(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Williams %R."""
    return await momentum.calculate_williams(data, params)

@mcp.tool()
async def calculate_cmo(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: CMO."""
    return await momentum.calculate_cmo(data, params)

@mcp.tool()
async def calculate_coppock(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Coppock Curve."""
    return await momentum.calculate_coppock(data, params)

@mcp.tool()
async def calculate_fish(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Fisher Transform."""
    return await momentum.calculate_fish(data, params)

@mcp.tool()
async def calculate_kama(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: KAMA."""
    return await momentum.calculate_kama(data, params)

@mcp.tool()
async def calculate_vortex(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: Vortex."""
    return await momentum.calculate_vortex(data, params)

@mcp.tool()
async def calculate_kst(data: list[dict], params: dict = None) -> str:
    """MOMENTUM: KST."""
    return await momentum.calculate_kst(data, params)

# --- 4. TREND SHORTCUTS ---
@mcp.tool()
async def calculate_sma(data: list[dict], params: dict = None) -> str:
    """TREND: SMA."""
    return await trend.calculate_sma(data, params)

@mcp.tool()
async def calculate_ema(data: list[dict], params: dict = None) -> str:
    """TREND: EMA."""
    return await trend.calculate_ema(data, params)

@mcp.tool()
async def calculate_dema(data: list[dict], params: dict = None) -> str:
    """TREND: DEMA."""
    return await trend.calculate_dema(data, params)

@mcp.tool()
async def calculate_tema(data: list[dict], params: dict = None) -> str:
    """TREND: TEMA."""
    return await trend.calculate_tema(data, params)

@mcp.tool()
async def calculate_trima(data: list[dict], params: dict = None) -> str:
    """TREND: TRIMA."""
    return await trend.calculate_trima(data, params)

@mcp.tool()
async def calculate_wma(data: list[dict], params: dict = None) -> str:
    """TREND: WMA."""
    return await trend.calculate_wma(data, params)

@mcp.tool()
async def calculate_hma(data: list[dict], params: dict = None) -> str:
    """TREND: HMA."""
    return await trend.calculate_hma(data, params)

@mcp.tool()
async def calculate_zlema(data: list[dict], params: dict = None) -> str:
    """TREND: ZLEMA."""
    return await trend.calculate_zlema(data, params)

@mcp.tool()
async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """TREND: ADX."""
    return await trend.calculate_adx(data, params)

@mcp.tool()
async def calculate_ssma(data: list[dict], params: dict = None) -> str:
    """TREND: SSMA."""
    return await trend.calculate_ssma(data, params)

@mcp.tool()
async def calculate_smma(data: list[dict], params: dict = None) -> str:
    """TREND: SMMA."""
    return await trend.calculate_smma(data, params)

@mcp.tool()
async def calculate_frama(data: list[dict], params: dict = None) -> str:
    """TREND: FRAMA."""
    return await trend.calculate_frama(data, params)

@mcp.tool()
async def calculate_sar(data: list[dict], params: dict = None) -> str:
    """TREND: SAR."""
    return await trend.calculate_sar(data, params)

# --- 5. VOLATILITY ---
@mcp.tool()
async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: ATR."""
    return await volatility.calculate_atr(data, params)

@mcp.tool()
async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Bollinger Bands."""
    return await volatility.calculate_bbands(data, params)

@mcp.tool()
async def calculate_kc(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Keltner Channels."""
    return await volatility.calculate_kc(data, params)

@mcp.tool()
async def calculate_do(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Donchian Channels."""
    return await volatility.calculate_do(data, params)

@mcp.tool()
async def calculate_mobo(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: MOBO Bands."""
    return await volatility.calculate_mobo(data, params)

@mcp.tool()
async def calculate_tr(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: True Range."""
    return await volatility.calculate_tr(data, params)

@mcp.tool()
async def calculate_bbwidth(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: BB Width."""
    return await volatility.calculate_bbwidth(data, params)

@mcp.tool()
async def calculate_percent_b(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Percent B."""
    return await volatility.calculate_percent_b(data, params)

@mcp.tool()
async def calculate_apz(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: APZ."""
    return await volatility.calculate_apz(data, params)

@mcp.tool()
async def calculate_massi(data: list[dict], params: dict = None) -> str:
    """VOLATILITY: Mass Index."""
    return await volatility.calculate_massi(data, params)

# --- 6. VOLUME ---
@mcp.tool()
async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """VOLUME: OBV."""
    return await volume.calculate_obv(data, params)

@mcp.tool()
async def calculate_mfi(data: list[dict], params: dict = None) -> str:
    """VOLUME: MFI."""
    return await volume.calculate_mfi(data, params)

@mcp.tool()
async def calculate_adl(data: list[dict], params: dict = None) -> str:
    """VOLUME: ADL."""
    return await volume.calculate_adl(data, params)

@mcp.tool()
async def calculate_chaikin(data: list[dict], params: dict = None) -> str:
    """VOLUME: Chaikin Osc."""
    return await volume.calculate_chaikin(data, params)

@mcp.tool()
async def calculate_efi(data: list[dict], params: dict = None) -> str:
    """VOLUME: Force Index."""
    return await volume.calculate_efi(data, params)

@mcp.tool()
async def calculate_vpt(data: list[dict], params: dict = None) -> str:
    """VOLUME: Volume Price Trend."""
    return await volume.calculate_vpt(data, params)

@mcp.tool()
async def calculate_emv(data: list[dict], params: dict = None) -> str:
    """VOLUME: Ease of Movement."""
    return await volume.calculate_emv(data, params)

@mcp.tool()
async def calculate_nvi(data: list[dict], params: dict = None) -> str:
    """VOLUME: NVI."""
    return await volume.calculate_nvi(data, params)

@mcp.tool()
async def calculate_pvi(data: list[dict], params: dict = None) -> str:
    """VOLUME: PVI."""
    return await volume.calculate_pvi(data, params)

@mcp.tool()
async def calculate_vzo(data: list[dict], params: dict = None) -> str:
    """VOLUME: VZO."""
    return await volume.calculate_vzo(data, params)

# --- 7. EXOTICS & LEVELS ---
@mcp.tool()
async def calculate_wto(data: list[dict], params: dict = None) -> str:
    """EXOTIC: Wave Trend."""
    return await exotics.calculate_wto(data, params)

@mcp.tool()
async def calculate_stc(data: list[dict], params: dict = None) -> str:
    """EXOTIC: STC."""
    return await exotics.calculate_stc(data, params)

@mcp.tool()
async def calculate_ev_macd(data: list[dict], params: dict = None) -> str:
    """EXOTIC: Elastic Volume MACD."""
    return await exotics.calculate_ev_macd(data, params)

@mcp.tool()
async def calculate_alma(data: list[dict], params: dict = None) -> str:
    """EXOTIC: ALMA."""
    return await exotics.calculate_alma(data, params)

@mcp.tool()
async def calculate_vama(data: list[dict], params: dict = None) -> str:
    """EXOTIC: VAMA."""
    return await exotics.calculate_vama(data, params)

@mcp.tool()
async def calculate_pivot(data: list[dict], params: dict = None) -> str:
    """LEVELS: Pivot Points."""
    return await levels.calculate_pivot(data, params)

@mcp.tool()
async def calculate_fib_pivot(data: list[dict], params: dict = None) -> str:
    """LEVELS: Fibonacci Pivots."""
    return await levels.calculate_fib_pivot(data, params)

@mcp.tool()
async def calculate_basp(data: list[dict], params: dict = None) -> str:
    """PRESSURE: Buy/Sell Pressure."""
    return await pressure.calculate_basp(data, params)

@mcp.tool()
async def calculate_ebbp(data: list[dict], params: dict = None) -> str:
    """PRESSURE: Bull/Bear Power."""
    return await pressure.calculate_ebbp(data, params)

# --- 8. PHASES 3 & 4 (Clouds, Flow, Weighted, etc) ---
@mcp.tool()
async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """CLOUD: Ichimoku."""
    return await clouds.calculate_ichimoku(data, params)

@mcp.tool()
async def calculate_trix(data: list[dict], params: dict = None) -> str:
    """OSC: TRIX."""
    return await advanced_oscillators.calculate_trix(data, params)

@mcp.tool()
async def calculate_ift_rsi(data: list[dict], params: dict = None) -> str:
    """OSC: Inverse Fisher RSI."""
    return await advanced_oscillators.calculate_ift_rsi(data, params)

@mcp.tool()
async def calculate_sqzmi(data: list[dict], params: dict = None) -> str:
    """OSC: Squeeze Momentum."""
    return await advanced_oscillators.calculate_sqzmi(data, params)

@mcp.tool()
async def calculate_vfi(data: list[dict], params: dict = None) -> str:
    """FLOW: Volume Flow."""
    return await volume_flow.calculate_vfi(data, params)

@mcp.tool()
async def calculate_fve(data: list[dict], params: dict = None) -> str:
    """FLOW: Finite Volume Element."""
    return await volume_flow.calculate_fve(data, params)

@mcp.tool()
async def calculate_qstick(data: list[dict], params: dict = None) -> str:
    """FLOW: QStick."""
    return await volume_flow.calculate_qstick(data, params)

@mcp.tool()
async def calculate_msd(data: list[dict], params: dict = None) -> str:
    """MATH: Moving Std Dev."""
    return await volume_flow.calculate_msd(data, params)

@mcp.tool()
async def calculate_vwap_finta(data: list[dict], params: dict = None) -> str:
    """WEIGHTED: VWAP."""
    return await weighted.calculate_vwap(data, params)

@mcp.tool()
async def calculate_evwma(data: list[dict], params: dict = None) -> str:
    """WEIGHTED: EVWMA."""
    return await weighted.calculate_evwma(data, params)

@mcp.tool()
async def calculate_wobv(data: list[dict], params: dict = None) -> str:
    """WEIGHTED: Weighted OBV."""
    return await weighted.calculate_wobv(data, params)

@mcp.tool()
async def calculate_pzo(data: list[dict], params: dict = None) -> str:
    """ZONE: Price Zone Osc."""
    return await zones.calculate_pzo(data, params)

@mcp.tool()
async def calculate_cfi(data: list[dict], params: dict = None) -> str:
    """ZONE: Cumulative Force."""
    return await zones.calculate_cfi(data, params)

@mcp.tool()
async def calculate_tp(data: list[dict], params: dict = None) -> str:
    """MATH: Typical Price."""
    return await zones.calculate_tp(data, params)

@mcp.tool()
async def calculate_chandelier(data: list[dict], params: dict = None) -> str:
    """EXIT: Chandelier."""
    return await exits_math.calculate_chandelier(data, params)


if __name__ == "__main__":
    mcp.run()
