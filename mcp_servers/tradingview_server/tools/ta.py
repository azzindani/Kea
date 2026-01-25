
from tradingview_ta import TA_Handler, Interval, Exchange
from shared.mcp.protocol import ToolResult, TextContent
import json
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_ta_summary(arguments: dict) -> ToolResult:
    """
    Get high-level Technical Analysis Summary (Buy/Sell/Hold).
    Args:
        symbol (str): "AAPL", "BTCUSD"
        screener (str): "america", "crypto", "indonesia"
        exchange (str): "NASDAQ", "BINANCE", "IDX"
        interval (str): "1d", "4h", "1h", "15m", "1m"
    """
    symbol = arguments.get("symbol")
    screener = arguments.get("screener", "america")
    exchange = arguments.get("exchange", "NASDAQ")
    interval = arguments.get("interval", "1d")

    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=interval
        )
        analysis = handler.get_analysis()
        return ToolResult(content=[TextContent(text=json.dumps(analysis.summary, indent=2))])
    except Exception as e:
        logger.error(f"TA tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_oscillators(arguments: dict) -> ToolResult:
    """Get detailed Oscillator data (RSI, MACD, Stochastic)."""
    return _get_analysis_subset(arguments, "oscillators")

async def get_moving_averages(arguments: dict) -> ToolResult:
    """Get detailed Moving Average data (SMA, EMA)."""
    return _get_analysis_subset(arguments, "moving_averages")

async def get_indicators(arguments: dict) -> ToolResult:
    """Get raw indicator values."""
    return _get_analysis_subset(arguments, "indicators")

def _get_analysis_subset(args: dict, key: str) -> ToolResult:
    symbol = args.get("symbol")
    screener = args.get("screener", "america")
    exchange = args.get("exchange", "NASDAQ")
    interval = args.get("interval", "1d")
    
    try:
        handler = TA_Handler(
            symbol=symbol, screener=screener, exchange=exchange, interval=interval
        )
        analysis = handler.get_analysis()
        data = getattr(analysis, key)
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])
    except Exception as e:
        logger.error(f"TA tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
