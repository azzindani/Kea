
import pandas as pd
import numpy as np
import io
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

async def eda_auto(
    data_url: str = None, 
    data: dict = None, 
    target_column: str = None
) -> ToolResult:
    """Perform automatic Exploratory Data Analysis."""
    
    try:
        df = _load_dataframe({"data_url": data_url, "data": data})
        
        result = "# 📊 Automatic EDA Report\n\n"
        
        # Basic Info
        result += "## 1. Dataset Overview\n\n"
        result += f"- **Rows**: {df.shape[0]:,}\n"
        result += f"- **Columns**: {df.shape[1]}\n"
        result += f"- **Memory**: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n\n"
        
        # Data Types
        result += "## 2. Data Types\n\n"
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            result += f"- {dtype}: {count} columns\n"
        result += "\n"
        
        # Missing Values
        result += "## 3. Missing Values\n\n"
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        missing_df = pd.DataFrame({'Missing': missing, 'Percent': missing_pct})
        missing_df = missing_df[missing_df['Missing'] > 0].sort_values('Missing', ascending=False)
        
        if len(missing_df) > 0:
            result += "| Column | Missing | Percent |\n|--------|---------|--------|\n"
            for col, row in missing_df.iterrows():
                result += f"| {col} | {row['Missing']} | {row['Percent']}% |\n"
        else:
            result += "✅ No missing values!\n"
        result += "\n"
        
        # Numeric Summary
        result += "## 4. Numeric Column Statistics\n\n"
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            result += "```\n"
            result += df[numeric_cols].describe().round(2).to_string()
            result += "\n```\n\n"
        
        # Categorical Summary
        result += "## 5. Categorical Columns\n\n"
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols[:5]:  # Limit to 5
            unique = df[col].nunique()
            result += f"### {col}\n"
            result += f"- Unique values: {unique}\n"
            if unique <= 10:
                result += f"- Values: {df[col].value_counts().head(10).to_dict()}\n"
            result += "\n"
        
        # Target Analysis
        if target_column and target_column in df.columns:
            result += f"## 6. Target Variable: {target_column}\n\n"
            if df[target_column].dtype in [np.number]:
                result += f"- Mean: {df[target_column].mean():.4f}\n"
                result += f"- Std: {df[target_column].std():.4f}\n"
                result += f"- Min: {df[target_column].min():.4f}\n"
                result += f"- Max: {df[target_column].max():.4f}\n"
            else:
                result += f"- Value counts:\n```\n{df[target_column].value_counts().to_string()}\n```\n"
        
        # Duplicates
        result += "## 7. Duplicates\n\n"
        dup_count = df.duplicated().sum()
        result += f"- Duplicate rows: {dup_count} ({dup_count/len(df)*100:.2f}%)\n"
        
        return ToolResult(content=[TextContent(text=result)])
        
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in EDA: {str(e)}")], isError=True)

async def data_profiler(
    data_url: str, 
    minimal: bool = True
) -> ToolResult:
    """Generate detailed data profile report."""
    
    try:
        df = pd.read_csv(data_url)
        
        try:
            from ydata_profiling import ProfileReport
            
            profile = ProfileReport(df, minimal=minimal, title="Data Profile")
            description = profile.get_description()
            
            result = "# 📋 Data Profile Report\n\n"
            result += f"Generated using ydata-profiling\n\n"
            result += f"## Summary\n\n"
            result += f"- Variables: {description.table['n_var']}\n"
            result += f"- Observations: {description.table['n']}\n"
            result += f"- Missing cells: {description.table['n_cells_missing']}\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            # Fallback
            result = "# 📋 Basic Data Profile\n\n"
            result += "(Install ydata-profiling for full report)\n\n"
            result += f"## Shape\n{df.shape}\n\n"
            result += f"## Types\n```\n{df.dtypes.to_string()}\n```\n\n"
            result += f"## Stats\n```\n{df.describe().to_string()}\n```\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in Profiling: {str(e)}")], isError=True)
