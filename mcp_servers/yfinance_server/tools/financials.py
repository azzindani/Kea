
import yfinance as yf

import yfinance as yf
from shared.logging import get_logger

logger = get_logger(__name__)

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
            
        title = f"{freq.capitalize()} {type_.replace('_', ' ').title()}"
        return f"### {title} ({ticker})\n\n{df.to_markdown()}"
    except Exception as e:
        logger.error(f"Financials error for {ticker}: {e}")
        return f"Error: {str(e)}"

# Unrolled Tools
async def get_income_statement_annual(ticker: str) -> str:
    return await _get_stmt(ticker, "income", "annual")

async def get_income_statement_quarterly(ticker: str) -> str:
    return await _get_stmt(ticker, "income", "quarterly")

async def get_balance_sheet_annual(ticker: str) -> str:
    return await _get_stmt(ticker, "balance", "annual")

async def get_balance_sheet_quarterly(ticker: str) -> str:
    return await _get_stmt(ticker, "balance", "quarterly")

async def get_cash_flow_annual(ticker: str) -> str:
    return await _get_stmt(ticker, "cashflow", "annual")

async def get_cash_flow_quarterly(ticker: str) -> str:
    return await _get_stmt(ticker, "cashflow", "quarterly")

