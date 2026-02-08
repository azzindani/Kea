
import pandas_datareader.data as web

from shared.logging import get_logger
import pandas as pd
from pandas_datareader.nasdaq_trader import get_nasdaq_symbols

logger = get_logger(__name__)


async def get_nasdaq_symbol_list(query: str = None) -> str:
    """
    Get list of all symbols traded on Nasdaq (includes NYSE/AMEX).
    Returns metadata: Symbol, Security Name, ETF, Test Issue, etc.
    """
    try:
        # get_nasdaq_symbols() returns a DataFrame indexed by Symbol
        # PDR's get_nasdaq_symbols is broken in some versions (passing args to read_csv incorrectly)
        # We reimplement a robust version here
        try:
            return get_nasdaq_symbols()
        except TypeError:
            # Fallback for "read_csv() takes 1 positional argument but 2 were given"
            url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt"
            df = pd.read_csv(url, sep="|")
            
            # Clean up logic similar to PDR
            df = df[df['Test Issue'] == 'N']
            df = df[df['ETF'] == 'N'] # Optional, but standard PDR filtering often includes this
            # Actually PDR returns all, let's just return what we have with proper index
            df = df.set_index("Symbol") if "Symbol" in df.columns else df
            return df
        except Exception:
            # Secondary fallback if FTP fails
            raise
        
        # Filter options?
        # Maybe just return top N or filtering by query
        # query = arguments.get("query")
        
        if query:
            # Case insensitive search in Symbol or Security Name
            mask = df.index.astype(str).str.contains(query, case=False) | \
                   df['Security Name'].astype(str).str.contains(query, case=False)
            df = df[mask]
            
        return f"### Nasdaq Trader Symbols\nTotal: {len(df)}\n\n{df.head(100).to_markdown()}"
        
    except Exception as e:
        logger.error(f"Nasdaq Symbols error: {e}")
        return f"Error: {str(e)}"

