
import pandas as pd
import json
import json


def process_ohlcv(data_input) -> pd.DataFrame:
    """
    Convert Input Data to Pandas DataFrame compatible with Finta.
    Finta requires lowercase column names: 'open', 'high', 'low', 'close', 'volume'.
    """
    # 1. Parse JSON
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
    # Finta is strict about 'close', 'open', 'high', 'low' generally.
    required = ['close'] 
    for r in required:
        if r not in df.columns:
             # Try mapping 'c' -> 'close'
             if 'c' in df.columns: df.rename(columns={'c': 'close'}, inplace=True)
             else: raise ValueError(f"DataFrame missing '{r}' column.")
             
    # Handle others
    if 'h' in df.columns: df.rename(columns={'h': 'high'}, inplace=True)
    if 'l' in df.columns: df.rename(columns={'l': 'low'}, inplace=True)
    if 'o' in df.columns: df.rename(columns={'o': 'open'}, inplace=True)
    if 'v' in df.columns: df.rename(columns={'v': 'volume'}, inplace=True)

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
    """Convert Result DataFrame to JSON."""
    # If df is a Series, convert to DF
    if isinstance(df, pd.Series):
        df = df.to_frame()
        
    out_df = df.reset_index()
    out_df = out_df.where(pd.notnull(out_df), None)
    records = out_df.to_dict(orient='records')
    return json.dumps(records, default=str, indent=2)

