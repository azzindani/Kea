import pandas as pd
import numpy as np
from typing import List, Optional

async def distribution_plot(data_url: str, columns: Optional[List[str]] = None) -> str:
    """Create distribution/histogram plots."""
    try:
        df = pd.read_csv(data_url)
        
        if not columns:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()[:5]
        
        result = "# 📈 Distribution Analysis\n\n"
        
        for col in columns:
            if col in df.columns:
                data = df[col].dropna()
                
                result += f"## {col}\n\n"
                result += f"- **Count**: {len(data):,}\n"
                result += f"- **Mean**: {data.mean():.4f}\n"
                result += f"- **Median**: {data.median():.4f}\n"
                result += f"- **Std**: {data.std():.4f}\n"
                result += f"- **Skewness**: {data.skew():.4f}\n"
                result += f"- **Kurtosis**: {data.kurtosis():.4f}\n"
                
                # ASCII histogram
                hist, bins = np.histogram(data, bins=10)
                if len(hist) > 0: # Handle empty data
                    max_val = max(hist)
                    result += "\n### Histogram\n```\n"
                    # Handle division by zero if max_val is 0
                    if max_val == 0:
                        max_val = 1
                        
                    for i, h in enumerate(hist):
                        bar = "█" * int(h / max_val * 30)
                        result += f"{bins[i]:.1f} - {bins[i+1]:.1f} | {bar} ({h:,})\n"
                    result += "```\n\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
