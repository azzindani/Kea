import pandas as pd
import numpy as np

async def time_series_forecast(data_url: str, value_column: str, date_column: str = None, periods: int = 10) -> str:
    """Time series forecasting."""
    try:
        df = pd.read_csv(data_url)
        
        result = "# 📈 Time Series Forecast\n\n"
        
        # Handle date column
        if date_column and date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.sort_values(date_column)
        
        values = df[value_column].values
        
        # Simple moving average forecast
        window = min(5, len(values) // 2)
        # ma = pd.Series(values).rolling(window=window).mean() # Not used
        
        result += f"**Value Column**: {value_col}\n" if 'value_col' in locals() else f"**Value Column**: {value_column}\n"
        result += f"**Data Points**: {len(values)}\n"
        result += f"**Forecast Periods**: {periods}\n\n"
        
        # Last value and trend
        last_value = values[-1]
        trend = (values[-1] - values[0]) / len(values)
        
        result += "## Forecast\n\n"
        result += "| Period | Forecast |\n|--------|----------|\n"
        
        for i in range(1, periods + 1):
            forecast = last_value + (trend * i)
            result += f"| +{i} | {forecast:.2f} |\n"
        
        result += "\n## Statistics\n\n"
        result += f"- Mean: {np.mean(values):.2f}\n"
        result += f"- Std: {np.std(values):.2f}\n"
        result += f"- Trend: {'+' if trend > 0 else ''}{trend:.4f}/period\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
