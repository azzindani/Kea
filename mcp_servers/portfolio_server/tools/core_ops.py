import pandas as pd
import io
import json
import structlog
from typing import List, Dict, Union, Optional, Any

logger = structlog.get_logger()

# Data Loading Helpers

def _parse_prices(prices_input: Union[str, Dict, List]) -> pd.DataFrame:
    """Helper to parse various input formats into a Prices DataFrame."""
    try:
        if isinstance(prices_input, str):
            # Check if it's a file path
            if prices_input.endswith('.csv') and os.path.exists(prices_input):
                 df = pd.read_csv(prices_input, parse_dates=True, index_col=0)
            else:
                 # Assume JSON string
                 try:
                     data = json.loads(prices_input)
                     df = pd.DataFrame(data)
                     # if dict of dicts (dates as keys), orient might need check
                 except:
                     # Fallback: simple CSV string?
                     df = pd.read_csv(io.StringIO(prices_input), parse_dates=True, index_col=0)
        elif isinstance(prices_input, dict):
            df = pd.DataFrame(prices_input)
        elif isinstance(prices_input, list):
             df = pd.DataFrame(prices_input)
        else:
            raise ValueError("Unsupported price input format")
            
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
             # Try to find date col if not index
             if 'date' in df.columns.astype(str).str.lower():
                 date_col = [c for c in df.columns if str(c).lower() == 'date'][0]
                 df = df.set_index(date_col)
             
             df.index = pd.to_datetime(df.index)
        
        # Sort index
        df = df.sort_index()
        return df
    except Exception as e:
        logger.error("failed_to_parse_prices", error=str(e))
        raise ValueError(f"Failed to parse prices: {str(e)}")

import os

def load_prices_csv(file_path: str) -> str:
    """Load prices from CSV and return summary json (to verify)."""
    if not os.path.exists(file_path): raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_csv(file_path, parse_dates=True, index_col=0)
    return f"Loaded {len(df)} rows, {len(df.columns)} assets: {list(df.columns)}"

def load_prices_json(json_data: str) -> str:
    """Load prices from JSON string."""
    df = _parse_prices(json_data)
    return f"Loaded {len(df)} rows, {len(df.columns)} assets: {list(df.columns)}"

def validate_tickers(prices_input: str) -> Dict[str, Any]:
    """Check data quality (missing values)."""
    df = _parse_prices(prices_input)
    missing = df.isnull().sum()
    return {
        "total_rows": len(df),
        "assets": list(df.columns),
        "missing_values": missing[missing > 0].to_dict(),
        "is_valid": int(missing.sum()) == 0
    }

def get_latest_prices(prices_input: str) -> Dict[str, float]:
    """Get the most recent price for each asset."""
    df = _parse_prices(prices_input)
    return df.iloc[-1].to_dict()

def calculate_returns(prices_input: str, log_returns: bool = False) -> str:
    """Calculate returns DataFrame as JSON."""
    df = _parse_prices(prices_input)
    if log_returns:
        import numpy as np
        rets = np.log(df / df.shift(1))
    else:
        rets = df.pct_change()
    rets = rets.dropna()
    return rets.to_json(orient="split", date_format="iso")
