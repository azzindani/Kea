import pandas as pd
import numpy as np
from typing import List, Optional

async def pairplot(data_url: str, columns: Optional[List[str]] = None, color_column: str = None) -> str:
    """Create pairwise scatter plot matrix."""
    try:
        df = pd.read_csv(data_url)
        
        if not columns:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()[:4]
        
        result = "# 🔗 Pairplot Analysis\n\n"
        result += f"**Columns**: {columns}\n"
        if color_column:
            result += f"**Color by**: {color_column}\n"
        result += "\n"
        
        # Basic stats for pairs
        result += "## Pairwise Statistics\n\n"
        result += "| Pair | Correlation | Interpretation |\n|------|-------------|----------------|\n"
        
        for i, col1 in enumerate(columns):
            for col2 in columns[i+1:]:
                if col1 in df.columns and col2 in df.columns:
                    # Filter only numeric columns for correlation calculation
                    if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
                        corr = df[col1].corr(df[col2])
                        if abs(corr) > 0.7:
                            interp = "Strong"
                        elif abs(corr) > 0.4:
                            interp = "Moderate"
                        else:
                            interp = "Weak"
                        result += f"| {col1} vs {col2} | {corr:.3f} | {interp} |\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
