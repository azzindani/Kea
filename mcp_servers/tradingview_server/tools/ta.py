
from tradingview_ta import TA_Handler, Interval, Exchange
from shared.mcp.protocol import ToolResult, TextContent
import json
from shared.logging.main import get_logger

logger = get_logger(__name__)


async def get_ta_summary(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """
    Get high-level Technical Analysis Summary (Buy/Sell/Hold).
    Args:
        symbol (str): "AAPL", "BTCUSD"
        screener (str): "america", "crypto", "indonesia"
        exchange (str): "NASDAQ", "BINANCE", "IDX"
        interval (str): "1d", "4h", "1h", "15m", "1m"
    """
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=interval
        )
        analysis = handler.get_analysis()
        return json.dumps(analysis.summary, indent=2)
    except Exception as e:
        logger.error(f"TA tool error: {e}")
        return f"Error: {str(e)}"

async def get_oscillators(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get detailed Oscillator data (RSI, MACD, Stochastic)."""
    return _get_analysis_subset(symbol, screener, exchange, interval, "oscillators")

async def get_moving_averages(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get detailed Moving Average data (SMA, EMA)."""
    return _get_analysis_subset(symbol, screener, exchange, interval, "moving_averages")

async def get_indicators(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get raw indicator values."""
    return _get_analysis_subset(symbol, screener, exchange, interval, "indicators")

def _get_analysis_subset(symbol: str, screener: str, exchange: str, interval: str, key: str) -> str:
    try:
        handler = TA_Handler(
            symbol=symbol, screener=screener, exchange=exchange, interval=interval
        )
        analysis = handler.get_analysis()
        data = getattr(analysis, key)
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"TA tool error: {e}")
        return f"Error: {str(e)}"

