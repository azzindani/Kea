
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

# Import Tools
from mcp_servers.pandas_ta_server.tools.bulk import (
    get_all_indicators, get_momentum_suite, get_trend_suite, 
    get_volatility_suite, get_volume_suite,
    get_candle_patterns_suite, get_statistics_suite
)
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator
from mcp_servers.pandas_ta_server.tools.signals import generate_signals
from mcp_servers.pandas_ta_server.tools.performance import (
    calculate_log_return, calculate_percent_return, calculate_drawdown
)
from mcp_servers.pandas_ta_server.tools.cycles import calculate_ebsw
from mcp_servers.pandas_ta_server.tools.backtest import simple_backtest
from mcp_servers.pandas_ta_server.tools.alpha import (
    calculate_rsx, calculate_thermo, calculate_massi, calculate_ui, calculate_natr
)
from mcp_servers.pandas_ta_server.tools.ml import construct_ml_dataset
from mcp_servers.pandas_ta_server.tools.spectral import calculate_fisher, calculate_cg
from mcp_servers.pandas_ta_server.tools.signals import calculate_tsignals as calculate_chop # Alias as we implemented chop there
# Actually we didn't export calculate_chop from signals, we exported calculate_tsignals but changed implementation to chop?
# Let's fix import mapping below
from mcp_servers.pandas_ta_server.tools.signals import calculate_tsignals # Renamed logic inside to call chop

# Correction: In signals.py I defined 'calculate_tsignals' which calls 'chop'.
# So I import calculate_tsignals as calculate_chop
from mcp_servers.pandas_ta_server.tools.signals import calculate_tsignals as calculate_chop

# Shortcuts
from mcp_servers.pandas_ta_server.tools.momentum import (
    calculate_rsi, calculate_macd, calculate_stoch, calculate_cci, calculate_roc,
    calculate_ao, calculate_apo, calculate_mom, calculate_tsi, calculate_uo,
    calculate_stochrsi, calculate_squeeze
)
from mcp_servers.pandas_ta_server.tools.trend import (
    calculate_sma, calculate_ema, calculate_wma, calculate_hma, calculate_adx,
    calculate_supertrend, calculate_vortex, calculate_aroon, calculate_dpo, calculate_psar,
    calculate_ichimoku
)
from mcp_servers.pandas_ta_server.tools.volatility_volume import (
    calculate_bbands, calculate_atr, calculate_kc, calculate_donchian, calculate_accbands,
    calculate_obv, calculate_cmf, calculate_mfi, calculate_vwap, calculate_adl,
    calculate_pvi, calculate_nvi
)
from mcp_servers.pandas_ta_server.tools.candles import (
    calculate_cdl_doji, calculate_cdl_hammer, calculate_cdl_engulfing,
    calculate_cdl_morningstar, calculate_cdl_eveningstar
)

logger = get_logger(__name__)

class PandasTAServer(MCPServer):
    """
    Pandas TA MCP Server.
    Provides 50+ Technical Analysis Tools.
    """
    
    def __init__(self) -> None:
        super().__init__(name="pandas_ta_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Bulk / Multitalent (High Value)
        self.register_tool(name="get_all_indicators", description="BULK: Calculate 100+ Indicators (All Strategies).", handler=get_all_indicators, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_momentum_suite", description="BULK: All Momentum Indicators.", handler=get_momentum_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_trend_suite", description="BULK: All Trend Indicators.", handler=get_trend_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_volatility_suite", description="BULK: All Volatility Indicators.", handler=get_volatility_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_volume_suite", description="BULK: All Volume Indicators.", handler=get_volume_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_candle_patterns_suite", description="BULK: All Candle Patterns (60+).", handler=get_candle_patterns_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_statistics_suite", description="BULK: All Statistics (Z-Score, Skew).", handler=get_statistics_suite, parameters={"data": {"type": "array"}})
        
        # 2. Universal & Signals
        self.register_tool(name="calculate_indicator", description="UNIVERSAL: Calculate Any Indicator.", handler=calculate_indicator, parameters={"data": {"type": "array"}, "indicator": {"type": "string"}, "params": {"type": "object"}})
        self.register_tool(name="generate_signals", description="LOGIC: Query Data (e.g. 'RSI_14 < 30').", handler=generate_signals, parameters={"data": {"type": "array"}, "condition": {"type": "string"}})
        
        # 3. Phase 3: Performance, Cycles, Backtest
        self.register_tool(name="calculate_log_return", description="PERF: Log Returns.", handler=calculate_log_return, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_percent_return", description="PERF: Percent Returns.", handler=calculate_percent_return, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_drawdown", description="PERF: Drawdown.", handler=calculate_drawdown, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ebsw", description="CYCLE: Even Better Sine Wave.", handler=calculate_ebsw, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="simple_backtest", description="BACKTEST: Run Strategy.", handler=simple_backtest, parameters={"data": {"type": "array"}, "entry_signal": {"type": "string"}, "exit_signal": {"type": "string"}})
        
        # 4. Phase 4: Alpha & ML
        self.register_tool(name="calculate_rsx", description="ALPHA: Jurik RSX.", handler=calculate_rsx, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_thermo", description="ALPHA: Elder's Thermometer.", handler=calculate_thermo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_massi", description="ALPHA: Mass Index.", handler=calculate_massi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ui", description="ALPHA: Ulcer Index.", handler=calculate_ui, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_natr", description="ALPHA: Normalized ATR.", handler=calculate_natr, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="construct_ml_dataset", description="ML: Create Features & Targets.", handler=construct_ml_dataset, parameters={"data": {"type": "array"}, "lags": {"type": "array"}})
        
        # 5. Phase 5: Spectral & Advanced
        self.register_tool(name="calculate_fisher", description="SPECTRAL: Fisher Transform.", handler=calculate_fisher, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_cg", description="SPECTRAL: Center of Gravity.", handler=calculate_cg, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_chop", description="TREAND: Choppiness Index.", handler=calculate_chop, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_pvi", description="VOLUME: Positive Volume Index.", handler=calculate_pvi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_nvi", description="VOLUME: Negative Volume Index.", handler=calculate_nvi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        
        # 6. Momentum Shortcuts
        self.register_tool(name="calculate_rsi", description="MOMENTUM: RSI.", handler=calculate_rsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_macd", description="MOMENTUM: MACD.", handler=calculate_macd, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_stoch", description="MOMENTUM: Stochastic.", handler=calculate_stoch, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_cci", description="MOMENTUM: CCI.", handler=calculate_cci, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_roc", description="MOMENTUM: ROC.", handler=calculate_roc, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ao", description="MOMENTUM: AO.", handler=calculate_ao, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_apo", description="MOMENTUM: APO.", handler=calculate_apo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_mom", description="MOMENTUM: Momentum.", handler=calculate_mom, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_tsi", description="MOMENTUM: TSI.", handler=calculate_tsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_uo", description="MOMENTUM: Ultimate Osc.", handler=calculate_uo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_stochrsi", description="MOMENTUM: StochRSI.", handler=calculate_stochrsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_squeeze", description="MOMENTUM: TTM Squeeze.", handler=calculate_squeeze, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 4. Trend Shortcuts
        self.register_tool(name="calculate_sma", description="TREND: SMA.", handler=calculate_sma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ema", description="TREND: EMA.", handler=calculate_ema, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_wma", description="TREND: WMA.", handler=calculate_wma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_hma", description="TREND: HMA.", handler=calculate_hma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_adx", description="TREND: ADX.", handler=calculate_adx, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_supertrend", description="TREND: Supertrend.", handler=calculate_supertrend, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vortex", description="TREND: Vortex.", handler=calculate_vortex, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_aroon", description="TREND: Aroon.", handler=calculate_aroon, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_dpo", description="TREND: DPO.", handler=calculate_dpo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_psar", description="TREND: Parabolic SAR.", handler=calculate_psar, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ichimoku", description="TREND: Ichimoku Cloud.", handler=calculate_ichimoku, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 5. Volatility & Volume Shortcuts (10)
        self.register_tool(name="calculate_bbands", description="VOLATILITY: Bollinger Bands.", handler=calculate_bbands, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_atr", description="VOLATILITY: ATR.", handler=calculate_atr, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_kc", description="VOLATILITY: Keltner Channels.", handler=calculate_kc, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_donchian", description="VOLATILITY: Donchian Channels.", handler=calculate_donchian, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_accbands", description="VOLATILITY: Acceleration Bands.", handler=calculate_accbands, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        
        self.register_tool(name="calculate_obv", description="VOLUME: On Balance Volume.", handler=calculate_obv, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_cmf", description="VOLUME: Chaikin Money Flow.", handler=calculate_cmf, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_mfi", description="VOLUME: Money Flow Index.", handler=calculate_mfi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vwap", description="VOLUME: VWAP.", handler=calculate_vwap, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_adl", description="VOLUME: Accumulation/Distribution.", handler=calculate_adl, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 6. Candle Shortcuts (5)
        self.register_tool(name="calculate_cdl_doji", description="CANDLE: Doji.", handler=calculate_cdl_doji, parameters={"data": {"type": "array"}})
        self.register_tool(name="calculate_cdl_hammer", description="CANDLE: Hammer.", handler=calculate_cdl_hammer, parameters={"data": {"type": "array"}})
        self.register_tool(name="calculate_cdl_engulfing", description="CANDLE: Engulfing.", handler=calculate_cdl_engulfing, parameters={"data": {"type": "array"}})
        self.register_tool(name="calculate_cdl_morningstar", description="CANDLE: Morning Star.", handler=calculate_cdl_morningstar, parameters={"data": {"type": "array"}})
        self.register_tool(name="calculate_cdl_eveningstar", description="CANDLE: Evening Star.", handler=calculate_cdl_eveningstar, parameters={"data": {"type": "array"}})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="pandas_ta_server"))
    server = PandasTAServer()
    logger.info(f"Starting PandasTAServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
