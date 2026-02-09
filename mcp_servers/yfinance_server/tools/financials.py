import yfinance as yf
import pandas as pd
from shared.logging import get_logger

logger = get_logger(__name__)

# Helper to avoid repetition

import pandas as pd

# Helper: Format huge numbers
def _format_financials(df: pd.DataFrame) -> pd.DataFrame:
    """Format large numbers in DataFrame to readable strings."""
    def fmt(x):
        if isinstance(x, (int, float)):
            if abs(x) >= 1e12:
                return f"{x/1e12:.2f}T"
            elif abs(x) >= 1e9:
                return f"{x/1e9:.2f}B"
            elif abs(x) >= 1e6:
                return f"{x/1e6:.2f}M"
        return x
    # Compatibility for pandas >= 2.1.0
    if hasattr(df, "map"):
        return df.map(fmt)
    else:
        return df.applymap(fmt)

# Helper to avoid repetition
async def _get_stmt(ticker: str, type_: str, freq: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        if type_ == "income":
            df = stock.quarterly_income_stmt if freq == "quarterly" else stock.income_stmt
        elif type_ == "balance":
            df = stock.quarterly_balance_sheet if freq == "quarterly" else stock.balance_sheet
        elif type_ == "cashflow":
            df = stock.quarterly_cashflow if freq == "quarterly" else stock.cashflow
        else:
            return "Error: Unknown Type"
            
        if df.empty:
            return f"No {type_} data found for {ticker}"
            
        # Format numbers
        df_formatted = _format_financials(df)
        
        title = f"{freq.capitalize()} {type_.replace('_', ' ').title()}"
        source = f"https://finance.yahoo.com/quote/{ticker}/{type_}"
        
        return f"### {title} ({ticker})\n\n{df_formatted.to_markdown()}\n\nSource: {source}"
    except Exception as e:
        logger.error(f"Financials error for {ticker}: {e}")
        return f"Error: {str(e)}"

# Unrolled Tools
async def get_income_statement_annual(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "income", "annual")

async def get_income_statement_quarterly(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "income", "quarterly")

async def get_balance_sheet_annual(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "balance", "annual")

async def get_balance_sheet_quarterly(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "balance", "quarterly")

async def get_cash_flow_statement_annual(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "cashflow", "annual")

async def get_cash_flow_statement_quarterly(ticker: str, **kwargs) -> str:
    return await _get_stmt(ticker, "cashflow", "quarterly")

