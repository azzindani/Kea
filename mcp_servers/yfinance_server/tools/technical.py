
import pandas as pd
import yfinance as yf
from shared.mcp.protocol import ToolResult, TextContent

async def get_simple_moving_average(arguments: dict) -> ToolResult:
    """Calculate SMA (Simple Moving Average)."""
    ticker = arguments.get("ticker")
    window = int(arguments.get("window", 20))
    try:
        # Fetch enough history
        # (window + 10) to have data
        hist = yf.Ticker(ticker).history(period="1y") 
        if hist.empty: return ToolResult(isError=True, content=[TextContent(text="No data")])
        
        sma = hist['Close'].rolling(window=window).mean().iloc[-1]
        return ToolResult(content=[TextContent(text=f"{sma:.4f}")])
    except Exception as e: return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_rsi(arguments: dict) -> ToolResult:
    """Calculate RSI (Relative Strength Index)."""
    ticker = arguments.get("ticker")
    window = int(arguments.get("window", 14))
    try:
        hist = yf.Ticker(ticker).history(period="6mo")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        
        return ToolResult(content=[TextContent(text=f"{val:.2f}")])
    except Exception as e: return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_macd(arguments: dict) -> ToolResult:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ticker = arguments.get("ticker")
    try:
        hist = yf.Ticker(ticker).history(period="1y")
        # Standard 12, 26, 9
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        res = {
            "macd": macd.iloc[-1],
            "signal": signal.iloc[-1],
            "histogram": macd.iloc[-1] - signal.iloc[-1]
        }
        return ToolResult(content=[TextContent(text=str(res))])
    except Exception as e: return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_bollinger_bands(arguments: dict) -> ToolResult:
    """Calculate Bollinger Bands (Upper, Middle, Lower)."""
    ticker = arguments.get("ticker")
    window = int(arguments.get("window", 20))
    try:
        hist = yf.Ticker(ticker).history(period="1y")
        sma = hist['Close'].rolling(window=window).mean()
        std = hist['Close'].rolling(window=window).std()
        
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        res = {
            "upper": upper.iloc[-1],
            "middle": sma.iloc[-1],
            "lower": lower.iloc[-1]
        }
        return ToolResult(content=[TextContent(text=str(res))])
    except Exception as e: return ToolResult(isError=True, content=[TextContent(text=str(e))])
