
import pandas as pd
import numpy as np
from scipy import stats
from shared.mcp.protocol import ToolResult, TextContent

def _load_dataframe(args: dict) -> pd.DataFrame:
    """Helper to load DataFrame from args."""
    if "data_url" in args and args["data_url"]:
        return pd.read_csv(args["data_url"])
    elif "data" in args and args["data"]:
        data = args["data"]
        if isinstance(data, dict) and "columns" in data and "rows" in data:
            return pd.DataFrame(data["rows"], columns=data["columns"])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError("Invalid data format. Expected {columns: [], rows: []} or list of dicts")
    else:
        raise ValueError("Either data_url or data must be provided")

async def correlation_matrix(
    data_url: str = None, 
    data: dict = None, 
    method: str = "pearson", 
    threshold: float = 0.0
) -> ToolResult:
    """Compute correlation matrix for numeric columns."""
    
    try:
        df = _load_dataframe({"data_url": data_url, "data": data})
        numeric_df = df.select_dtypes(include=[np.number])
        
        corr = numeric_df.corr(method=method)
        
        result = f"# 📈 Correlation Matrix ({method})\n\n"
        
        # Full matrix
        result += "## Full Matrix\n```\n"
        result += corr.round(3).to_string()
        result += "\n```\n\n"
        
        # High correlations
        if threshold > 0:
            result += f"## Correlations > {threshold}\n\n"
            high_corr = []
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    val = abs(corr.iloc[i, j])
                    if val >= threshold:
                        high_corr.append({
                            'col1': corr.columns[i],
                            'col2': corr.columns[j],
                            'correlation': corr.iloc[i, j]
                        })
            
            if high_corr:
                high_corr.sort(key=lambda x: abs(x['correlation']), reverse=True)
                result += "| Column 1 | Column 2 | Correlation |\n|----------|----------|-------------|\n"
                for item in high_corr:
                    result += f"| {item['col1']} | {item['col2']} | {item['correlation']:.3f} |\n"
            else:
                result += "No correlations above threshold.\n"
        
        return ToolResult(content=[TextContent(text=result)])
        
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in Correlation: {str(e)}")], isError=True)

async def statistical_test(
    data_url: str, 
    test_type: str, 
    column1: str = None, 
    column2: str = None, 
    group_column: str = None
) -> ToolResult:
    """Run statistical tests on data."""
    
    try:
        df = pd.read_csv(data_url)
        
        result = f"# 📊 Statistical Test: {test_type}\n\n"
        
        if test_type == "ttest" and column1 and column2:
            data1 = df[column1].dropna()
            data2 = df[column2].dropna()
            stat, pvalue = stats.ttest_ind(data1, data2)
            
            result += f"## T-Test: {column1} vs {column2}\n\n"
            result += f"- t-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "anova" and column1 and group_column:
            groups = [group[column1].dropna() for name, group in df.groupby(group_column)]
            stat, pvalue = stats.f_oneway(*groups)
            
            result += f"## ANOVA: {column1} by {group_column}\n\n"
            result += f"- F-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "chi2" and column1 and column2:
            contingency = pd.crosstab(df[column1], df[column2])
            stat, pvalue, dof, expected = stats.chi2_contingency(contingency)
            
            result += f"## Chi-Square: {column1} vs {column2}\n\n"
            result += f"- χ² statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Degrees of freedom: {dof}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "normality" and column1:
            data = df[column1].dropna()
            stat, pvalue = stats.shapiro(data[:5000])  # Limit for large datasets
            
            result += f"## Normality Test (Shapiro-Wilk): {column1}\n\n"
            result += f"- W-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Normal distribution: {'Yes' if pvalue > 0.05 else 'No'}\n"
        else:
            result += "Invalid test configuration. Check required parameters.\n"
        
        return ToolResult(content=[TextContent(text=result)])
        
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in Statistical Test: {str(e)}")], isError=True)
