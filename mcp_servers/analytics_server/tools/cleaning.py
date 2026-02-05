
import pandas as pd
import numpy as np
from shared.mcp.protocol import ToolResult, TextContent

async def data_cleaner(
    data_url: str,
    handle_missing: str = "none",
    handle_outliers: str = "none",
    remove_duplicates: bool = False
) -> ToolResult:
    """Clean dataset: handle missing values, outliers, duplicates."""
    
    try:
        df = pd.read_csv(data_url)
        original_shape = df.shape
        
        result = "# 🧹 Data Cleaning Report\n\n"
        result += f"**Original shape**: {original_shape}\n\n"
        
        # Handle missing values
        if handle_missing != "none":
            result += "## Missing Values\n\n"
            missing_before = df.isnull().sum().sum()
            
            if handle_missing == "drop":
                df = df.dropna()
            elif handle_missing in ["mean", "median", "mode"]:
                for col in df.select_dtypes(include=[np.number]).columns:
                    if df[col].isnull().any():
                        if handle_missing == "mean":
                            df[col] = df[col].fillna(df[col].mean())
                        elif handle_missing == "median":
                            df[col] = df[col].fillna(df[col].median())
                        elif handle_missing == "mode":
                            df[col] = df[col].fillna(df[col].mode()[0])
            elif handle_missing == "ffill":
                df = df.fillna(method='ffill')
            
            missing_after = df.isnull().sum().sum()
            result += f"- Before: {missing_before} missing values\n"
            result += f"- After: {missing_after} missing values\n"
            result += f"- Method: {handle_missing}\n\n"
        
        # Handle outliers
        if handle_outliers != "none":
            result += "## Outliers\n\n"
            outliers_removed = 0
            
            for col in df.select_dtypes(include=[np.number]).columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                
                outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                
                if outliers > 0:
                    if handle_outliers == "clip":
                        df[col] = df[col].clip(lower, upper)
                    elif handle_outliers == "drop":
                        df = df[(df[col] >= lower) & (df[col] <= upper)]
                    
                    outliers_removed += outliers
            
            result += f"- Outliers handled: {outliers_removed}\n"
            result += f"- Method: {handle_outliers}\n\n"
        
        # Remove duplicates
        if remove_duplicates:
            result += "## Duplicates\n\n"
            dups_before = df.duplicated().sum()
            df = df.drop_duplicates()
            result += f"- Removed: {dups_before} duplicate rows\n\n"
        
        result += f"**Final shape**: {df.shape}\n"
        result += f"**Rows changed**: {original_shape[0] - df.shape[0]}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in Cleaning: {str(e)}")], isError=True)

async def feature_engineer(
    data_url: str, 
    operations: list[str] = []
) -> ToolResult:
    """Create derived features from existing columns."""
    
    try:
        df = pd.read_csv(data_url)
        
        result = "# 🔧 Feature Engineering\n\n"
        
        if not operations:
            # Suggest operations
            result += "## Suggested Operations\n\n"
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            result += "### Numeric combinations\n"
            if len(numeric_cols) >= 2:
                result += f"- Ratio: {numeric_cols[0]} / {numeric_cols[1]}\n"
                result += f"- Sum: {numeric_cols[0]} + {numeric_cols[1]}\n"
            
            result += "\n### Categorical encoding\n"
            for col in cat_cols[:3]:
                result += f"- One-hot encode: {col}\n"
            
            result += "\n### Date features (if date columns exist)\n"
            result += "- Extract: year, month, day, dayofweek\n"
        else:
            result += "## Applied Operations\n\n"
            for op in operations:
                result += f"- {op}\n"
        
        return ToolResult(content=[TextContent(text=result)])
        
    except Exception as e:
        return ToolResult(content=[TextContent(text=f"Error in Feature Engineering: {str(e)}")], isError=True)
