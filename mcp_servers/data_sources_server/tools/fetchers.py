
import os
import pandas as pd
from shared.logging import get_logger

logger = get_logger(__name__)

async def fetch_yfinance(symbol: str, period: str = "1mo", interval: str = "1d", data_type: str = "history") -> str:
    """Fetch data from Yahoo Finance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        
        if data_type == "history":
            df = ticker.history(period=period, interval=interval)
            result = f"## {symbol} Price History\n\n"
            result += f"Period: {period}, Interval: {interval}\n"
            result += f"Rows: {len(df)}\n\n"
            result += "### Latest Data\n```\n"
            result += df.tail(10).to_string()
            result += "\n```\n"
            
        elif data_type == "info":
            info = ticker.info
            result = f"## {symbol} Company Info\n\n"
            key_fields = ['shortName', 'sector', 'industry', 'marketCap', 
                         'trailingPE', 'dividendYield', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']
            for field in key_fields:
                if field in info:
                    result += f"- **{field}**: {info[field]}\n"
                    
        elif data_type == "financials":
            df = ticker.financials
            result = f"## {symbol} Financials\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
            
        elif data_type == "balance_sheet":
            df = ticker.balance_sheet
            result = f"## {symbol} Balance Sheet\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
            
        elif data_type == "cashflow":
            df = ticker.cashflow
            result = f"## {symbol} Cash Flow\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
        else:
            result = f"Unknown data_type: {data_type}"
        
        return result
    except Exception as e:
        logger.error(f"YFinance error: {e}")
        return f"Error: {e}"

async def fetch_fred(series_id: str, start_date: str = None, end_date: str = None) -> str:
    """Fetch data from FRED."""
    try:
        from fredapi import Fred
        
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            return "FRED_API_KEY not set"
        
        fred = Fred(api_key=api_key)
        
        data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        
        result = f"## FRED: {series_id}\n\n"
        result += f"Observations: {len(data)}\n\n"
        result += "### Latest Values\n```\n"
        result += data.tail(20).to_string()
        result += "\n```\n"
        
        return result
        
    except ImportError:
        return "fredapi not installed. Run: pip install fredapi"
    except Exception as e:
        logger.error(f"FRED error: {e}")
        return f"Error: {e}"

async def fetch_world_bank(indicator: str, country: str = "all", start_year: int = None, end_year: int = None) -> str:
    """Fetch data from World Bank."""
    try:
        import wbgapi as wb
        
        time_range = None
        if start_year and end_year:
            time_range = range(start_year, end_year + 1)
        
        if country == "all":
            data = wb.data.DataFrame(indicator, time=time_range, labels=True)
        else:
            data = wb.data.DataFrame(indicator, economy=country, time=time_range, labels=True)
        
        result = f"## World Bank: {indicator}\n\n"
        result += f"Shape: {data.shape}\n\n"
        result += "### Data\n```\n"
        result += data.head(20).to_string()
        result += "\n```\n"
        
        return result
        
    except ImportError:
        return "wbgapi not installed. Run: pip install wbgapi"
    except Exception as e:
        logger.error(f"World Bank error: {e}")
        return f"Error: {e}"

async def fetch_csv(url: str, preview_rows: int = 5) -> str:
    """Fetch CSV from URL."""
    try:
        df = pd.read_csv(url)
        
        result = f"## CSV Data from URL\n\n"
        result += f"**URL**: {url}\n\n"
        result += f"**Shape**: {df.shape[0]} rows × {df.shape[1]} columns\n\n"
        
        result += "### Columns\n"
        for col in df.columns:
            dtype = df[col].dtype
            nulls = df[col].isnull().sum()
            result += f"- `{col}` ({dtype}) - {nulls} nulls\n"
        
        result += f"\n### Preview (first {preview_rows} rows)\n```\n"
        result += df.head(preview_rows).to_string()
        result += "\n```\n"
        
        result += "\n### Statistics\n```\n"
        result += df.describe().to_string()
        result += "\n```\n"
        
        return result
    except Exception as e:
        logger.error(f"CSV Fetch error: {e}")
        return f"Error: {e}"
