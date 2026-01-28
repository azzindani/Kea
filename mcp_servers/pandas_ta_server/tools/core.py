
import pandas as pd
import pandas_ta as ta
import json
import json


def process_ohlcv(data_input) -> pd.DataFrame:
    """
    Convert Input Data (List of Dicts or JSON String) to Pandas DataFrame.
    Expected Columns: open, high, low, close, volume (case insensitive).
    Returns DataFrame indexed by datetime (if 'date'/'time' present) or integer.
    """
    # 1. Parse JSON if string
    if isinstance(data_input, str):
        try:
            data = json.loads(data_input)
        except:
             raise ValueError("Invalid JSON data string.")
    else:
        data = data_input

    if not isinstance(data, list):
         raise ValueError("Data must be a list of dictionaries (OHLCV).")

    if not data:
         raise ValueError("Empty data list.")

    # 2. Create DataFrame
    df = pd.DataFrame(data)
    
    # 3. Normalize Columns (Lower case)
    df.columns = [c.lower() for c in df.columns]
    
    # 4. Check Required Columns
    # Some indicators only need close, but standard is OHLCV
    # We won't enforce all, but pandas_ta needs at least 'close' usually.
    if 'close' not in df.columns:
         # Try mapping 'c' -> 'close'? No, stick to explicit names.
         raise ValueError("DataFrame missing 'close' column.")

    # 5. Handle Datetime
    date_cols = [c for c in df.columns if c in ['date', 'time', 'timestamp', 'datetime']]
    if date_cols:
        col = date_cols[0]
        df[col] = pd.to_datetime(df[col])
        df.set_index(col, inplace=True)
    
    # 6. Ensure Numeric
    cols_to_numeric = ['open', 'high', 'low', 'close', 'volume']
    for c in cols_to_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
            
    return df


def df_to_json(df: pd.DataFrame, title: str = "TA Result") -> str:
    """
    Convert Result DataFrame to JSON text.
    Handles NaN values (fills with None/Null for JSON).
    """
    # Reset index to include Date in output
    out_df = df.reset_index()
    
    # Convert Timestamp to string
    # Replace NaN with None (which becomes null in JSON)
    out_df = out_df.where(pd.notnull(out_df), None)
    
    records = out_df.to_dict(orient='records')
    
    return json.dumps(records, default=str, indent=2)

