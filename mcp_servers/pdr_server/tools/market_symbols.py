
import pandas_datareader.data as web
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd
from pandas_datareader.nasdaq_trader import get_nasdaq_symbols

logger = get_logger(__name__)

async def get_nasdaq_symbol_list(arguments: dict) -> ToolResult:
    """
    Get list of all symbols traded on Nasdaq (includes NYSE/AMEX).
    Returns metadata: Symbol, Security Name, ETF, Test Issue, etc.
    """
    try:
        # get_nasdaq_symbols() returns a DataFrame indexed by Symbol
        df = get_nasdaq_symbols()
        
        # Filter options?
        # Maybe just return top N or filtering by query
        query = arguments.get("query")
        
        if query:
            # Case insensitive search in Symbol or Security Name
            mask = df.index.astype(str).str.contains(query, case=False) | \
                   df['Security Name'].astype(str).str.contains(query, case=False)
            df = df[mask]
            
        return ToolResult(content=[TextContent(text=f"### Nasdaq Trader Symbols\nTotal: {len(df)}\n\n{df.head(100).to_markdown()}")])
        
    except Exception as e:
        logger.error(f"Nasdaq Symbols error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
