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
                    
                    # --- UNWRAP FASTMCP ENVELOPE ---
                    if isinstance(data, dict) and "status" in data and "data" in data:
                        if data["status"] == "error":
                            raise ValueError(f"Server error: {data.get('data')}")
                        data = data["data"]
                    
                    if isinstance(data, str):
                        # Data might be a double-encoded JSON string
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            # Not JSON, maybe raw CSV string to be handled by fallback
                            pass
                    
                    if isinstance(data, dict) and all(k in data for k in ("columns", "index", "data")):
                        df = pd.DataFrame(data["data"], index=data["index"], columns=data["columns"])
                    else:
                        df = pd.DataFrame(data)
                except ValueError as e:
                    raise e
                except Exception:
                    # Fallback: simple CSV string?
                    try:
                        df = pd.read_csv(io.StringIO(str(prices_input)), parse_dates=True, index_col=0)
                    except:
                        raise ValueError(f"Could not parse prices input: {str(prices_input)[:100]}...")
        elif isinstance(prices_input, dict):
            # Check for envelope in dict form
            data = prices_input
            if "status" in data and "data" in data:
                data = data["data"]
            df = pd.DataFrame(data)
        elif isinstance(prices_input, list):
             df = pd.DataFrame(prices_input)
        else:
            raise ValueError("Unsupported price input format")
            
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
             # Try to find date col if not index
             # Check columns (might be strings if loaded from JSON)
             cols = [str(c).lower() for c in df.columns]
             if 'date' in cols:
                 date_col = df.columns[cols.index('date')]
                 df = df.set_index(date_col)
             elif 'index' in cols: # Split orient json handling
                 index_col = df.columns[cols.index('index')]
                 df = df.set_index(index_col)
             
             df.index = pd.to_datetime(df.index)
        
        # Sort index
        df = df.sort_index()
        # Drop columns that are not assets (like 'index' or 'date' if they remained)
        df = df.select_dtypes(include=['number'])
        return df
    except Exception as e:
        logger.error("failed_to_parse_prices", error=str(e))
        raise ValueError(f"Failed to parse prices: {str(e)}")

import os

def load_prices_csv(file_path: str) -> str:
    """Load prices from CSV and return as JSON string."""
    if not os.path.exists(file_path): raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_csv(file_path, parse_dates=True, index_col=0)
    # Return as JSON to be passed to other tools
    return df.to_json(orient="split", date_format="iso")

def load_prices_json(json_data: str) -> str:
    """Load prices from JSON string."""
    df = _parse_prices(json_data)
    return df.to_json(orient="split", date_format="iso")

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
