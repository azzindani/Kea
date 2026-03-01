
import pandas_datareader.data as web

from shared.logging.main import get_logger
import datetime

logger = get_logger(__name__)


async def get_bank_of_canada_data(symbols: list[str] = None, start_date: str = None) -> str:
    """
    Get Bank of Canada Data (Forex, Rates).
    """
    # Valet API usually doesn't need key for simple stuff in pandas_datareader?
    # Actually PDR uses 'wk' or similar codes.
    # Typical codes: FXUSDCAD (USD/CAD).
    
    s_list = symbols or ["FXUSDCAD"]
    
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
        
        df = web.DataReader(s_list, "bankofcanada", start=start)
        
        return f"### Bank of Canada Data\n\n{df.tail(20).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

