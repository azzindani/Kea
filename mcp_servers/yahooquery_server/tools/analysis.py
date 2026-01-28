
from mcp_servers.yahooquery_server.tools.ticker import SmartTicker
from shared.mcp.protocol import ToolResult, TextContent, FileContent
from shared.logging import get_logger
import pandas as pd
import uuid

logger = get_logger(__name__)


async def get_history_bulk(tickers: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Bulk Download Historical Data.
    Args:
        tickers (list[str] | str): Symbols
        period (str): "1mo", "1y", "ytd", "max"
        interval (str): "1d", "1wk", "1mo"
    """
    
    try:
        st = SmartTicker(tickers, asynchronous=True)
        # YahooQuery's history returns a MultiIndex DataFrame (symbol, date)
        df = st.yq.history(period=period, interval=interval)
        
        if isinstance(df, dict):
             # Usually means error or single result dict
             return str(df)
             
        if df.empty:
             return "No data found"

        # Reset index to make it flat CSV-friendly (Symbol, Date, Open, High...)
        df_flat = df.reset_index()
        
        # Save to file for robustness with large bulk
        report_id = uuid.uuid4().hex[:8]
        file_path = f"/tmp/yq_history_{report_id}.csv"
        df_flat.to_csv(file_path, index=False)
        
        count = len(tickers.split()) if isinstance(tickers, str) else len(tickers)
        return f"Fetched history for {count} tickers. Rows: {len(df)}. Data saved to file: {file_path}"
        
    except Exception as e:
        logger.error(f"History error: {e}")
        return f"Error: {str(e)}"

