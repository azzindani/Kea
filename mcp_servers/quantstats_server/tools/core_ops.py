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
        data_to_parse = returns_input
        
        # 1. Handle String Input (JSON/CSV)
        if isinstance(returns_input, str):
            try:
                # Try JSON
                parsed = json.loads(returns_input)
                
                # Unwrap FastMCP envelope if present
                if isinstance(parsed, dict) and "data" in parsed and "status" in parsed:
                    data_to_parse = parsed["data"]
                    # If data is still a string, try parsing it again
                    if isinstance(data_to_parse, str):
                        try:
                            data_to_parse = json.loads(data_to_parse)
                        except:
                            pass
                else:
                    data_to_parse = parsed
            except:
                # Not JSON, maybe CSV or raw string
                data_to_parse = returns_input

        # 2. Convert to Series
        if isinstance(data_to_parse, dict):
            series = pd.Series(data_to_parse)
        elif isinstance(data_to_parse, list):
            series = pd.Series(data_to_parse)
        elif isinstance(data_to_parse, str):
            # Try CSV
            try:
                df = pd.read_csv(io.StringIO(data_to_parse), parse_dates=True, index_col=0)
                series = df.iloc[:, 0]
            except:
                raise ValueError("Could not parse string input as JSON or CSV.")
        else:
            series = pd.Series(data_to_parse)

        # 3. Ensure DatetimeIndex
        if not isinstance(series.index, pd.DatetimeIndex):
            try:
                series.index = pd.to_datetime(series.index)
            except:
                # If it's just a range index, we might need to assume frequency or fail
                # But typically it should have dates.
                pass
        
        # Ensure it is a Series
        if not isinstance(series, pd.Series):
            series = pd.Series(series)

        # Ensure numeric and drop NaNs
        series = pd.to_numeric(series, errors='coerce').dropna()
        
        # Ensure name for quantstats
        if not series.name:
            series.name = "Returns"
            
        # Ensure proper sort
        series = series.sort_index()
        
        return series
    
    except Exception as e:
        logger.error("failed_to_parse_returns", error=str(e))
        raise ValueError(f"Failed to parse returns: {str(e)}") from e

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
