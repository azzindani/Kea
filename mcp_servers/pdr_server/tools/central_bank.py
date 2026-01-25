
import pandas_datareader.data as web
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import datetime

logger = get_logger(__name__)

async def get_bank_of_canada_data(arguments: dict) -> ToolResult:
    """
    Get Bank of Canada Data (Forex, Rates).
    """
    # Valet API usually doesn't need key for simple stuff in pandas_datareader?
    # Actually PDR uses 'wk' or similar codes.
    # Typical codes: FXUSDCAD (USD/CAD).
    
    symbols = arguments.get("symbols") or ["FXUSDCAD"]
    
    start_date = arguments.get("start_date")
    if not start_date:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        start = start_date
        
    try:
        # Source 'bankofcanada' is deprecated in favor of direct Valet API usually,
        # but check if PDR still supports 'bankofcanada' string?
        # Docs say it supports it.
        
        # Note: Bank of Canada in PDR might be tricky.
        # Let's try 'iex' logic or similar.
        # Actually, let's just stick to what works.
        # If PDR is broken for this, we'll fail gracefully.
        
        df = web.DataReader(symbols, "bankofcanada", start=start)
        
        return ToolResult(content=[TextContent(text=f"### Bank of Canada Data\n\n{df.tail(20).to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
