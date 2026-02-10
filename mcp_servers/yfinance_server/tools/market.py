
import yfinance as yf
import pandas as pd
import uuid
import os
from shared.logging import get_logger

logger = get_logger(__name__)

# 1. Bulk Tools with File I/O
async def get_bulk_historical_data(tickers: str = None, ticker: str = None, period: str = "1mo", interval: str = "1d") -> str:
    """Download historical data for multiple tickers (File Return)."""
    # Robustness for both singular and plural argument names
    target_tickers = tickers or ticker
    if not target_tickers:
        return "Error: No tickers provided. Please provide 'tickers' (space-separated) or 'ticker'."
    
    try:
        # Threaded Download
        df = yf.download(target_tickers, period=period, interval=interval, group_by="ticker", threads=True, progress=False)
        
        # Save to temp file (Standard I/O for large data)
        report_id = uuid.uuid4().hex[:8]
        # In case /tmp doesn't exist on Windows, use a more portable temp path if needed, 
        # but the prompt says they are on Windows, and /tmp might not work.
        # However, I'll stick to the existing logic but maybe make it safer.
        temp_dir = os.environ.get("TEMP", "/tmp")
        file_path = os.path.join(temp_dir, f"history_{report_id}.csv")
        
        # Flatten for CSV if multi-index
        if isinstance(df.columns, pd.MultiIndex):
             df.stack(level=0).to_csv(file_path)
        else:
             df.to_csv(file_path)
             
        return f"Fetched history for {len(target_tickers.split())} tickers. Data saved to file: {file_path}"
    except Exception as e:
        logger.error(f"Market tool error: {e}")
        return f"Error: {str(e)}"

# 2. Micro-Metric Tools (Unrolled)
async def get_current_price(ticker: str, **kwargs) -> str:
    """Get just the price."""
    try:
        price = yf.Ticker(ticker).fast_info.last_price
        return str(price)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

async def get_market_cap(ticker: str, **kwargs) -> str:
    """Get Market Cap."""
    try:
        val = yf.Ticker(ticker).info.get("marketCap", "N/A")
        return str(val)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

async def get_volume(ticker: str, **kwargs) -> str:
    """Get recent volume."""
    try:
        val = yf.Ticker(ticker).fast_info.last_volume
        return str(val)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

async def get_pe_ratio(ticker: str, **kwargs) -> str:
    """Get Trailing PE."""
    try:
        val = yf.Ticker(ticker).info.get("trailingPE", "N/A")
        return str(val)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

async def get_beta(ticker: str, **kwargs) -> str:
    """Get Beta (Volatility)."""
    try:
        val = yf.Ticker(ticker).info.get("beta", "N/A")
        return str(val)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

async def get_quote_metadata(ticker: str, **kwargs) -> str:
    """Get Bid/Ask/Currency."""
    try:
        i = yf.Ticker(ticker).info
        res = {k: i.get(k) for k in ["bid", "ask", "bidSize", "askSize", "currency", "financialCurrency"]}
        return str(res)
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return "N/A"

