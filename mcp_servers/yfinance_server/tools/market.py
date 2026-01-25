
import yfinance as yf
import pandas as pd
import uuid
import os
from shared.mcp.protocol import ToolResult, TextContent, FileContent
from shared.logging import get_logger

logger = get_logger(__name__)

# 1. Bulk Tools with File I/O
async def get_bulk_historical_data(arguments: dict) -> ToolResult:
    """Download historical data for multiple tickers (File Return)."""
    tickers = arguments.get("tickers") # "AAPL MSFT"
    period = arguments.get("period", "1mo")
    interval = arguments.get("interval", "1d")
    
    try:
        # Threaded Download
        df = yf.download(tickers, period=period, interval=interval, group_by="ticker", threads=True, progress=False)
        
        # Save to temp file (Standard I/O for large data)
        report_id = uuid.uuid4().hex[:8]
        file_path = f"/tmp/history_{report_id}.csv"
        # Flatten for CSV if multi-index
        if isinstance(df.columns, pd.MultiIndex):
             df.stack(level=0).to_csv(file_path)
        else:
             df.to_csv(file_path)
             
        # Create artifacts metadata
        return ToolResult(content=[
            TextContent(text=f"Fetched history for {len(tickers.split())} tickers. Data saved to file."),
            FileContent(
                path=file_path,
                mimeType="text/csv",
                description=f"Historical Data ({period}) for {tickers}"
            )
        ])
    except Exception as e:
        logger.error(f"Market tool error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# 2. Micro-Metric Tools (Unrolled)
async def get_current_price(arguments: dict) -> ToolResult:
    """Get just the price."""
    ticker = arguments.get("ticker")
    try:
        price = yf.Ticker(ticker).fast_info.last_price
        return ToolResult(content=[TextContent(text=str(price))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])

async def get_market_cap(arguments: dict) -> ToolResult:
    """Get Market Cap."""
    ticker = arguments.get("ticker")
    try:
        val = yf.Ticker(ticker).info.get("marketCap", "N/A")
        return ToolResult(content=[TextContent(text=str(val))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])

async def get_volume(arguments: dict) -> ToolResult:
    """Get recent volume."""
    ticker = arguments.get("ticker")
    try:
        val = yf.Ticker(ticker).fast_info.last_volume
        return ToolResult(content=[TextContent(text=str(val))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])

async def get_pe_ratio(arguments: dict) -> ToolResult:
    """Get Trailing PE."""
    ticker = arguments.get("ticker")
    try:
        val = yf.Ticker(ticker).info.get("trailingPE", "N/A")
        return ToolResult(content=[TextContent(text=str(val))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])

async def get_beta(arguments: dict) -> ToolResult:
    """Get Beta (Volatility)."""
    ticker = arguments.get("ticker")
    try:
        val = yf.Ticker(ticker).info.get("beta", "N/A")
        return ToolResult(content=[TextContent(text=str(val))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])

async def get_quote_metadata(arguments: dict) -> ToolResult:
    """Get Bid/Ask/Currency."""
    ticker = arguments.get("ticker")
    try:
        i = yf.Ticker(ticker).info
        res = {k: i.get(k) for k in ["bid", "ask", "bidSize", "askSize", "currency", "financialCurrency"]}
        return ToolResult(content=[TextContent(text=str(res))])
    except: 
        logger.error(f"Market tool error (N/A fallback)")
        return ToolResult(isError=True, content=[TextContent(text="N/A")])
