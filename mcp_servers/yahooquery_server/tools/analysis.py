
from mcp_servers.yahooquery_server.tools.ticker import SmartTicker
from shared.mcp.protocol import ToolResult, TextContent, FileContent
from shared.logging import get_logger
import pandas as pd
import uuid

logger = get_logger(__name__)

async def get_history_bulk(arguments: dict) -> ToolResult:
    """
    Bulk Download Historical Data.
    Args:
        tickers (list[str]): Symbols
        period (str): "1mo", "1y", "ytd", "max"
        interval (str): "1d", "1wk", "1mo"
    """
    tickers = arguments.get("tickers")
    period = arguments.get("period", "1mo")
    interval = arguments.get("interval", "1d")
    
    try:
        st = SmartTicker(tickers, asynchronous=True)
        # YahooQuery's history returns a MultiIndex DataFrame (symbol, date)
        df = st.yq.history(period=period, interval=interval)
        
        if isinstance(df, dict):
             # Usually means error or single result dict
             return ToolResult(content=[TextContent(text=str(df))])
             
        if df.empty:
             return ToolResult(isError=True, content=[TextContent(text="No data found")])

        # Reset index to make it flat CSV-friendly (Symbol, Date, Open, High...)
        df_flat = df.reset_index()
        
        # Save to file for robustness with large bulk
        report_id = uuid.uuid4().hex[:8]
        file_path = f"/tmp/yq_history_{report_id}.csv"
        df_flat.to_csv(file_path, index=False)
        
        return ToolResult(content=[
            TextContent(text=f"Fetched history for {len(tickers) if isinstance(tickers, list) else 1} tickers. Rows: {len(df)}"),
            FileContent(path=file_path, mimeType="text/csv", description=f"Bulk History ({period})")
        ])
        
    except Exception as e:
        logger.error(f"History error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
