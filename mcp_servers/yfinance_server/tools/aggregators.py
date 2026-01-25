
import yfinance as yf
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_full_ticker_report(arguments: dict) -> ToolResult:
    """
    MULTI-TALENT: Get Price, Info, Financials, Holders in one go.
    Saves 5+ round trips.
    """
    ticker = arguments.get("ticker")
    
    try:
        stock = yf.Ticker(ticker)
        
        # Parallel fetch if we wanted to be fancy, but yfinance lazy loads mostly
        info = stock.info
        price = info.get("currentPrice", "N/A")
        
        # Financials (Last year)
        try:
           fin = stock.financials.iloc[:, 0].to_dict() # Most recent column
        except:
           fin = "N/A"
           
        # Holders
        try:
           holders = stock.major_holders.to_markdown()
        except:
           holders = "N/A"
           
        report = f"""
# 📑 Full Report: {ticker}

## 1. Snapshot
**Price**: {price} {info.get("currency", "")}
**Sector**: {info.get("sector", "N/A")}
**Market Cap**: {info.get("marketCap", "N/A")}

## 2. Key Financials (Last Reported)
{str(fin)[:1000]}...

## 3. Ownership
{holders}

## 4. Business Summary
{info.get("longBusinessSummary", "")[:500]}...
"""
        return ToolResult(content=[TextContent(text=report)])
        
    except Exception as e:
        logger.error(f"Aggregator error: {e}")
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
