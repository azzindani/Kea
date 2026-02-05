
from finvizfinance.quote import finvizfinance

from shared.logging import get_logger
import pandas as pd

logger = get_logger(__name__)


async def get_finviz_statement(ticker: str, statement: str = "I", timeframe: str = "A") -> str:
    """
    Get Financial Statements from Finviz.
    statement: "I" (Income), "B" (Balance), "C" (Cash Flow)
    timeframe: "A" (Annual), "Q" (Quarterly)
    """
    # ticker = arguments.get("ticker")
    # statement = arguments.get("statement", "I")
    # timeframe = arguments.get("timeframe", "A")
    
    try:
        stock = finvizfinance(ticker)
        # Assuming get_statements or similar exists in Quote or Statements module.
        # Based on research: finvizfinance.quote.Statements
        
        # Let's try the direct method on the stock object if available, 
        # likely stock.client.get_statements or we treat stock as Quote object.
        # Research said: Statements.get_statements(ticker, ...)
        
        from finvizfinance.quote import Statements
        
        inst = Statements()
        df = inst.get_statements(ticker=ticker, statement=statement, timeframe=timeframe)
        
        return f"### Finviz Statement: {ticker} ({statement}/{timeframe})\n\n{df.to_markdown()}"
        
    except Exception as e:
        logger.error(f"Financials error {ticker}: {e}")
        return f"Error: {str(e)}"

