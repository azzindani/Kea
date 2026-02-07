import quantstats as qs
import pandas as pd
import io
import json
import structlog
from typing import Union, List, Dict, Any

import math

def safe_float(val: Any) -> float:
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except:
        return 0.0

logger = structlog.get_logger()

# Extend pandas with quantstats (standard practice)
qs.extend_pandas()

def _parse_returns(returns_input: Union[str, float, Dict, List]) -> pd.Series:
    """Helper to parse input into a Returns Series."""
    try:
        if isinstance(returns_input, str):
            # Ticker check? 
            # Ideally if it looks like a ticker (e.g. "AAPL", "^GSPC"), we download.
            # But inputs should differ (e.g. `ticker` vs `data`). 
            
            if len(returns_input) < 10 and returns_input.isalnum():
                # Treat as ticker shorthand if short and clean? 
                # Better to be explicit in tool args. 
                # Here we assume data string (json/csv).
                try:
                    # JSON?
                    data = json.loads(returns_input)
                    if isinstance(data, dict):
                        # Dictionary {date: value}
                        series = pd.Series(data)
                        series.index = pd.to_datetime(series.index)
                    elif isinstance(data, list):
                        series = pd.Series(data) 
                except:
                    # CSV?
                    try:
                        df = pd.read_csv(io.StringIO(returns_input), parse_dates=True, index_col=0)
                        # Assume first column is returns
                        series = df.iloc[:, 0]
                    except:
                        raise ValueError("Could not parse string input as JSON or CSV.")
            else:
                 # Try json load first for long strings
                try:
                    data = json.loads(returns_input)
                    series = pd.Series(data)
                    series.index = pd.to_datetime(series.index)
                except:
                     # Fallback CSV
                    df = pd.read_csv(io.StringIO(returns_input), parse_dates=True, index_col=0)
                    series = df.iloc[:, 0]

        elif isinstance(returns_input, dict):
            series = pd.Series(returns_input)
            series.index = pd.to_datetime(series.index)
        elif isinstance(returns_input, list):
            series = pd.Series(returns_input)
        else:
            raise ValueError("Unsupported data type")
            
        # Ensure proper sort and numeric
        series = series.sort_index()
        series = pd.to_numeric(series, errors='coerce').dropna()
        return series
    
    except Exception as e:
        logger.error("failed_to_parse_returns", error=str(e))
        raise ValueError(f"Failed to parse returns: {str(e)}")

def download_returns(ticker: str, period: str = "max") -> str:
    """Download market returns for a ticker via yfinance."""
    # qs.utils.download_returns handles cleaning
    series = qs.utils.download_returns(ticker, period=period)
    return series.to_json(orient='split', date_format='iso')

def load_returns_csv(file_path: str) -> str:
    """Load returns from a local CSV file."""
    # Expecting Date index, Returns col
    df = pd.read_csv(file_path, parse_dates=True, index_col=0)
    series = df.iloc[:, 0]
    return series.to_json(orient='split', date_format='iso')

def load_returns_json(json_data: str) -> str:
    """Load returns from JSON string."""
    series = _parse_returns(json_data)
    return series.to_json(orient='split', date_format='iso')

def make_index(returns_input: str, initial_value: float = 100.0) -> str:
    """Rebases the return series to a starting value (e.g. 100)."""
    series = _parse_returns(returns_input)
    # (1 + r).cumprod() * start
    index = (1 + series).cumprod() * initial_value
    # Prepend starting value? QS typically does this in plots.
    # We will return the series aligned with dates.
    return index.to_json(orient='split', date_format='iso')

def to_drawdown_series(returns_input: str) -> str:
    """Convert returns to drawdown series."""
    series = _parse_returns(returns_input)
    dd = qs.stats.to_drawdown_series(series)
    return dd.to_json(orient='split', date_format='iso')
