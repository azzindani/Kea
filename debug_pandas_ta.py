
import pandas as pd
import pandas_ta as ta

def debug():
    df = pd.DataFrame({"close": [1, 2, 3], "open": [1, 2, 3], "high": [1, 2, 3], "low": [1, 2, 3], "volume": [100, 100, 100]})
    print("Pandas Version:", pd.__version__)
    print("Pandas TA Version:", ta.version)
    
    print("\n--- df.ta attributes ---")
    try:
        print(dir(df.ta))
    except Exception as e:
        print(f"Error inspecting df.ta: {e}")
        
    print("\n--- Checking strategy existence ---")
    if hasattr(df.ta, "strategy"):
        print("df.ta.strategy EXISTS")
    else:
        print("df.ta.strategy MISSING")
        
    # Check if we can run a single indicator
    print("\n--- Running RSI ---")
    try:
        df.ta.rsi(append=True)
        print("RSI Success columns:", df.columns)
    except Exception as e:
        print("RSI Failed:", e)

if __name__ == "__main__":
    debug()
