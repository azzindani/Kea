
import pandas as pd
import yfinance as yf
import numpy as np
from typing import List, Optional
from shared.logging.main import get_logger

logger = get_logger(__name__)

async def get_analyst_recommendations(ticker: str, **kwargs) -> str:
    """Get analyst recommendations."""
    try:
        df = yf.Ticker(ticker).recommendations
        return df.to_markdown() if df is not None and not df.empty else "N/A"
    except Exception as e:
        logger.error(f"Error in recommendations for {ticker}: {e}")
        return f"Error: {str(e)}"

async def get_price_targets(ticker: str, **kwargs) -> str:
    """Get analyst price targets."""
    try:
        info = yf.Ticker(ticker).info
        targets = {k: info.get(k) for k in ["targetHighPrice", "targetLowPrice", "targetMeanPrice", "targetMedianPrice", "numberOfAnalystOpinions"]}
        return str(targets)
    except Exception as e:
        logger.error(f"Error in price targets for {ticker}: {e}")
        return f"Error: {str(e)}"

async def get_earnings_calendar(ticker: str, **kwargs) -> str:
    """Get earnings calendar."""
    try:
        cal = yf.Ticker(ticker).calendar
        return str(cal)
    except Exception as e:
        logger.error(f"Error in calendar for {ticker}: {e}")
        return f"Error: {str(e)}"

async def get_upgrades_downgrades(ticker: str, **kwargs) -> str:
    """Get upgrades and downgrades."""
    try:
        df = yf.Ticker(ticker).upgrades_downgrades
        return df.head(20).to_markdown() if df is not None and not df.empty else "N/A"
    except Exception as e:
        logger.error(f"Error in upgrades for {ticker}: {e}")
        return f"Error: {str(e)}"

async def get_dividends_history(ticker: str, **kwargs) -> str:
    """Get dividends history."""
    try:
        s = yf.Ticker(ticker).dividends
        return s.to_markdown() if s is not None and not s.empty else "N/A"
    except Exception as e:
        logger.error(f"Error in dividends for {ticker}: {e}")
        return f"Error: {str(e)}"

async def get_splits_history(ticker: str, **kwargs) -> str:
    """Get splits history."""
    try:
        s = yf.Ticker(ticker).splits
        return s.to_markdown() if s is not None and not s.empty else "N/A"
    except Exception as e:
        logger.error(f"Error in splits for {ticker}: {e}")
        return f"Error: {str(e)}"

async def calculate_indicators(ticker: str, indicators: List[str] = ["sma", "rsi"], period: str = "1y", interval: str = "1d", **kwargs) -> str:
    """
    Calculate technical indicators for a given ticker.
    Args:
        ticker (str): "AAPL", "BBCA.JK"
        indicators (list[str]): ["sma", "ema", "rsi", "macd", "bbands"] (default: ["sma", "rsi"])
        period (str): "1y" (default)
        interval (str): "1d" (default)
    """
    # Robustness for generic test calls
    ticker = ticker or kwargs.get("symbol", "")
    if not ticker:
        return "Error: No ticker provided."
    
    # Handle indicators if passed as string by accident or missing
    if not indicators:
        indicators = ["sma", "rsi"]
    
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        if df.empty:
            return f"No data found for {ticker}"
            
        # Ensure we have data
        # Calculate requested indicators using Standard Pandas
        
        summary = []
        close = df['Close']
        
        if "sma" in indicators:
            # Simple Moving Average (20, 50, 200)
            df['SMA_20'] = close.rolling(window=20).mean()
            df['SMA_50'] = close.rolling(window=50).mean()
            df['SMA_200'] = close.rolling(window=200).mean()
            summary.append("Calculated SMA (20, 50, 200)")

        if "ema" in indicators:
            # Exponential Moving Average (12, 26)
            df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
            df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
            summary.append("Calculated EMA (12, 26)")

        if "rsi" in indicators:
            # RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI_14'] = 100 - (100 / (1 + rs))
            # Standard RSI usually uses Wilder's smoothing, but simple rolling is close enough for basic check, 
            # or we can do EWM:
            # gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
            # loss = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
            summary.append("Calculated RSI (14)")
            
        if "macd" in indicators:
            # MACD (12, 26, 9)
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            summary.append("Calculated MACD")
            
        if "bbands" in indicators:
            # Bollinger Bands (20, 2)
            sma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            df['BBL_20_2.0'] = sma20 - (std20 * 2)
            df['BBM_20_2.0'] = sma20
            df['BBU_20_2.0'] = sma20 + (std20 * 2)
            summary.append("Calculated Bollinger Bands")

        # Clean NaN values from the beginning
        output_df = df.tail(100) # Return last 100 rows to keep context acceptable
        
        # Convert to CSV string for the model to read
        csv_data = output_df.to_csv()
        
        return f"Technical indicators for {ticker} ({', '.join(summary)}):\n\n{csv_data}"

    except Exception as e:
        logger.error(f"Analysis failed for {ticker}: {e}")
        return f"Analysis failed: {str(e)}"

