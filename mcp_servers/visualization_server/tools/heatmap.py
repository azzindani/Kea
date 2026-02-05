import pandas as pd
import numpy as np

async def correlation_heatmap(data_url: str, title: str = "Correlation Heatmap") -> str:
    """Create correlation heatmap."""
    try:
        df = pd.read_csv(data_url)
        numeric_df = df.select_dtypes(include=[np.number])
        corr = numeric_df.corr()
        
        result = f"# 🔥 {title}\n\n"
        result += f"**Numeric Columns**: {len(numeric_df.columns)}\n\n"
        
        # ASCII heatmap
        result += "## Correlation Matrix\n\n"
        result += "```\n"
        result += corr.round(2).to_string()
        result += "\n```\n\n"
        
        # Highlight strong correlations
        result += "## Strong Correlations (|r| > 0.5)\n\n"
        strong = []
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) > 0.5:
                    strong.append({
                        'var1': corr.columns[i],
                        'var2': corr.columns[j],
                        'corr': val
                    })
        
        if strong:
            strong.sort(key=lambda x: abs(x['corr']), reverse=True)
            result += "| Variable 1 | Variable 2 | Correlation |\n|------------|------------|-------------|\n"
            for item in strong:
                emoji = "🟢" if item['corr'] > 0 else "🔴"
                result += f"| {item['var1']} | {item['var2']} | {emoji} {item['corr']:.3f} |\n"
        else:
            result += "No strong correlations found.\n"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
