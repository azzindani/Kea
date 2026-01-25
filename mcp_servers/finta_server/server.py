
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

# Import Tools
from mcp_servers.finta_server.tools.bulk import (
    get_all_indicators, get_momentum_suite, get_trend_suite, 
    get_volatility_suite, get_volume_suite
)
from mcp_servers.finta_server.tools.universal import calculate_indicator

# Shortcuts
from mcp_servers.finta_server.tools.momentum import (
    calculate_rsi, calculate_macd, calculate_stoch, calculate_tsi, calculate_uo,
    calculate_roc, calculate_mom, calculate_ao, calculate_williams, calculate_cmo,
    calculate_coppock, calculate_fish, calculate_kama, calculate_vortex, calculate_kst
)
from mcp_servers.finta_server.tools.trend import (
    calculate_sma, calculate_ema, calculate_dema, calculate_tema, calculate_trima,
    calculate_wma, calculate_hma, calculate_zlema, calculate_adx, calculate_ssma,
    calculate_smma, calculate_frama, calculate_sar
)
from mcp_servers.finta_server.tools.volatility import (
    calculate_atr, calculate_bbands, calculate_kc, calculate_do, calculate_mobo,
    calculate_tr, calculate_bbwidth, calculate_percent_b, calculate_apz, calculate_massi
)
from mcp_servers.finta_server.tools.volume import (
    calculate_obv, calculate_mfi, calculate_adl, calculate_chaikin, calculate_efi,
    calculate_vpt, calculate_emv, calculate_nvi, calculate_pvi, calculate_vzo
)
from mcp_servers.finta_server.tools.exotics import (
    calculate_wto, calculate_stc, calculate_ev_macd, calculate_alma, calculate_vama
)
from mcp_servers.finta_server.tools.levels import calculate_pivot, calculate_fib_pivot
from mcp_servers.finta_server.tools.pressure import calculate_basp, calculate_ebbp
# Phase 3
from mcp_servers.finta_server.tools.clouds import calculate_ichimoku
from mcp_servers.finta_server.tools.advanced_oscillators import (
    calculate_trix, calculate_ift_rsi, calculate_sqzmi, calculate_mi
)
from mcp_servers.finta_server.tools.volume_flow import (
    calculate_vfi, calculate_fve, calculate_qstick, calculate_msd
)
# Phase 4
from mcp_servers.finta_server.tools.weighted import calculate_vwap, calculate_evwma, calculate_wobv
from mcp_servers.finta_server.tools.zones import calculate_pzo, calculate_cfi, calculate_tp
from mcp_servers.finta_server.tools.exits_math import calculate_chandelier

logger = get_logger(__name__)

class FintaServer(MCPServer):
    """
    Finta MCP Server.
    Provides 50+ Technical Analysis Tools.
    """
    
    def __init__(self) -> None:
        super().__init__(name="finta_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Bulk / Multitalent (High Value)
        self.register_tool(name="get_all_indicators", description="BULK: Calculate 80+ Indicators.", handler=get_all_indicators, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_momentum_suite", description="BULK: All Momentum Indicators.", handler=get_momentum_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_trend_suite", description="BULK: All Trend Indicators.", handler=get_trend_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_volatility_suite", description="BULK: All Volatility Indicators.", handler=get_volatility_suite, parameters={"data": {"type": "array"}})
        self.register_tool(name="get_volume_suite", description="BULK: All Volume Indicators.", handler=get_volume_suite, parameters={"data": {"type": "array"}})
        
        # 2. Universal
        self.register_tool(name="calculate_indicator", description="UNIVERSAL: Calculate Any Indicator (SMA, RSI, etc).", handler=calculate_indicator, parameters={"data": {"type": "array"}, "indicator": {"type": "string"}, "params": {"type": "object"}})
        
        # 3. Momentum Shortcuts (15)
        self.register_tool(name="calculate_rsi", description="MOMENTUM: RSI.", handler=calculate_rsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_macd", description="MOMENTUM: MACD.", handler=calculate_macd, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_stoch", description="MOMENTUM: Stochastic.", handler=calculate_stoch, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_tsi", description="MOMENTUM: TSI.", handler=calculate_tsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_uo", description="MOMENTUM: Ultimate Osc.", handler=calculate_uo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_roc", description="MOMENTUM: Rate of Change.", handler=calculate_roc, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_mom", description="MOMENTUM: Momentum.", handler=calculate_mom, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ao", description="MOMENTUM: AO.", handler=calculate_ao, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_williams", description="MOMENTUM: Williams %R.", handler=calculate_williams, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_cmo", description="MOMENTUM: CMO.", handler=calculate_cmo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_coppock", description="MOMENTUM: Coppock Curve.", handler=calculate_coppock, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_fish", description="MOMENTUM: Fisher Transform.", handler=calculate_fish, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_kama", description="MOMENTUM: KAMA.", handler=calculate_kama, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vortex", description="MOMENTUM: Vortex.", handler=calculate_vortex, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_kst", description="MOMENTUM: KST.", handler=calculate_kst, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 4. Trend Shortcuts (13)
        self.register_tool(name="calculate_sma", description="TREND: SMA.", handler=calculate_sma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ema", description="TREND: EMA.", handler=calculate_ema, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_dema", description="TREND: DEMA.", handler=calculate_dema, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_tema", description="TREND: TEMA.", handler=calculate_tema, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_trima", description="TREND: TRIMA.", handler=calculate_trima, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_wma", description="TREND: WMA.", handler=calculate_wma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_hma", description="TREND: HMA.", handler=calculate_hma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_zlema", description="TREND: ZLEMA.", handler=calculate_zlema, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_adx", description="TREND: ADX.", handler=calculate_adx, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ssma", description="TREND: SSMA.", handler=calculate_ssma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_smma", description="TREND: SMMA.", handler=calculate_smma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_frama", description="TREND: FRAMA.", handler=calculate_frama, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_sar", description="TREND: SAR.", handler=calculate_sar, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 5. Volatility Shortcuts (10)
        self.register_tool(name="calculate_atr", description="VOLATILITY: ATR.", handler=calculate_atr, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_bbands", description="VOLATILITY: Bollinger Bands.", handler=calculate_bbands, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_kc", description="VOLATILITY: Keltner Channels.", handler=calculate_kc, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_do", description="VOLATILITY: Donchian Channels.", handler=calculate_do, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_mobo", description="VOLATILITY: MOBO Bands.", handler=calculate_mobo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_tr", description="VOLATILITY: True Range.", handler=calculate_tr, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_bbwidth", description="VOLATILITY: BB Width.", handler=calculate_bbwidth, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_percent_b", description="VOLATILITY: Percent B.", handler=calculate_percent_b, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_apz", description="VOLATILITY: APZ.", handler=calculate_apz, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_massi", description="VOLATILITY: Mass Index.", handler=calculate_massi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 6. Volume Shortcuts (10)
        self.register_tool(name="calculate_obv", description="VOLUME: OBV.", handler=calculate_obv, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_mfi", description="VOLUME: MFI.", handler=calculate_mfi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_adl", description="VOLUME: ADL.", handler=calculate_adl, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_chaikin", description="VOLUME: Chaikin Osc.", handler=calculate_chaikin, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_efi", description="VOLUME: Force Index.", handler=calculate_efi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vpt", description="VOLUME: Volume Price Trend.", handler=calculate_vpt, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_emv", description="VOLUME: Ease of Move.", handler=calculate_emv, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_nvi", description="VOLUME: NVI.", handler=calculate_nvi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_pvi", description="VOLUME: PVI.", handler=calculate_pvi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vzo", description="VOLUME: VZO.", handler=calculate_vzo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 7. Exotics & Levels (Phase 2)
        self.register_tool(name="calculate_wto", description="EXOTIC: Wave Trend.", handler=calculate_wto, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_stc", description="EXOTIC: STC.", handler=calculate_stc, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ev_macd", description="EXOTIC: Elastic Volume MACD.", handler=calculate_ev_macd, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_alma", description="EXOTIC: ALMA.", handler=calculate_alma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vama", description="EXOTIC: VAMA.", handler=calculate_vama, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        
        self.register_tool(name="calculate_pivot", description="LEVELS: Pivot Points.", handler=calculate_pivot, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_fib_pivot", description="LEVELS: Fibonacci Pivots.", handler=calculate_fib_pivot, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        
        self.register_tool(name="calculate_basp", description="PRESSURE: Buy/Sell Pressure.", handler=calculate_basp, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ebbp", description="PRESSURE: Bull/Bear Power.", handler=calculate_ebbp, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 8. Clouds & Flow (Phase 3)
        self.register_tool(name="calculate_ichimoku", description="CLOUD: Ichimoku.", handler=calculate_ichimoku, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_trix", description="OSC: TRIX.", handler=calculate_trix, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_ift_rsi", description="OSC: Inverse Fisher RSI.", handler=calculate_ift_rsi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_sqzmi", description="OSC: Squeeze Momentum.", handler=calculate_sqzmi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_vfi", description="FLOW: Volume Flow.", handler=calculate_vfi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_fve", description="FLOW: Finite Volume Element.", handler=calculate_fve, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_qstick", description="FLOW: QStick.", handler=calculate_qstick, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_msd", description="MATH: Moving Std Dev.", handler=calculate_msd, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

        # 9. Precision & Weighted (Phase 4)
        self.register_tool(name="calculate_vwap", description="WEIGHTED: VWAP.", handler=calculate_vwap, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_evwma", description="WEIGHTED: EVWMA.", handler=calculate_evwma, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_wobv", description="WEIGHTED: Weighted OBV.", handler=calculate_wobv, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_pzo", description="ZONE: Price Zone Osc.", handler=calculate_pzo, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_cfi", description="ZONE: Cumulative Force.", handler=calculate_cfi, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_tp", description="MATH: Typical Price.", handler=calculate_tp, parameters={"data": {"type": "array"}, "params": {"type": "object"}})
        self.register_tool(name="calculate_chandelier", description="EXIT: Chandelier.", handler=calculate_chandelier, parameters={"data": {"type": "array"}, "params": {"type": "object"}})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="finta_server"))
    server = FintaServer()
    logger.info(f"Starting FintaServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
