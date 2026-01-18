"""
Analytics MCP Server.

Provides tools for data analytics:
- EDA: automatic exploration, profiling
- Cleaning: missing values, outliers, duplicates
- Transformation: type conversion, feature engineering
- Statistical tests
"""

from __future__ import annotations

from typing import Any
import io
import json

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class AnalyticsServer(MCPServerBase):
    """MCP server for data analytics operations."""
    
    def __init__(self) -> None:
        super().__init__(name="analytics_server")
    
    def _load_dataframe(self, args: dict):
        """
        Load DataFrame from either data_url or inline data.
        
        Supports:
        - data_url: URL to CSV file
        - data: {"columns": [...], "rows": [[...], ...]}
        """
        import pandas as pd
        
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
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="eda_auto",
                description="Perform automatic Exploratory Data Analysis on a dataset",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "data": {"type": "object", "description": "Inline data: {columns: [], rows: []}"},
                        "target_column": {"type": "string", "description": "Optional target variable for analysis"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="data_profiler",
                description="Generate detailed data profile report",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "minimal": {"type": "boolean", "description": "Generate minimal report (faster)"},
                    },
                    required=["data_url"],
                ),
            ),
            Tool(
                name="data_cleaner",
                description="Clean dataset: handle missing values, outliers, duplicates",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "handle_missing": {"type": "string", "description": "Strategy: drop, mean, median, mode, ffill"},
                        "handle_outliers": {"type": "string", "description": "Strategy: none, clip, drop"},
                        "remove_duplicates": {"type": "boolean", "description": "Remove duplicate rows"},
                    },
                    required=["data_url"],
                ),
            ),
            Tool(
                name="correlation_matrix",
                description="Compute correlation matrix for numeric columns",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "data": {"type": "object", "description": "Inline data: {columns: [], rows: []}"},
                        "method": {"type": "string", "description": "Method: pearson, spearman, kendall"},
                        "threshold": {"type": "number", "description": "Only show correlations above threshold"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="statistical_test",
                description="Run statistical tests on data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "test_type": {"type": "string", "description": "Test: ttest, anova, chi2, normality"},
                        "column1": {"type": "string", "description": "First column"},
                        "column2": {"type": "string", "description": "Second column (if needed)"},
                        "group_column": {"type": "string", "description": "Group column for ANOVA"},
                    },
                    required=["data_url", "test_type"],
                ),
            ),
            Tool(
                name="feature_engineer",
                description="Create derived features from existing columns",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "operations": {"type": "array", "description": "List of operations: [{type, columns, name}]"},
                    },
                    required=["data_url"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "eda_auto":
                return await self._handle_eda_auto(arguments)
            elif name == "data_profiler":
                return await self._handle_profiler(arguments)
            elif name == "data_cleaner":
                return await self._handle_cleaner(arguments)
            elif name == "correlation_matrix":
                return await self._handle_correlation(arguments)
            elif name == "statistical_test":
                return await self._handle_statistical_test(arguments)
            elif name == "feature_engineer":
                return await self._handle_feature_engineer(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_eda_auto(self, args: dict) -> ToolResult:
        """Perform automatic EDA."""
        import pandas as pd
        import numpy as np
        
        df = self._load_dataframe(args)
        target = args.get("target_column")
        
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
        if target and target in df.columns:
            result += f"## 6. Target Variable: {target}\n\n"
            if df[target].dtype in [np.number]:
                result += f"- Mean: {df[target].mean():.4f}\n"
                result += f"- Std: {df[target].std():.4f}\n"
                result += f"- Min: {df[target].min():.4f}\n"
                result += f"- Max: {df[target].max():.4f}\n"
            else:
                result += f"- Value counts:\n```\n{df[target].value_counts().to_string()}\n```\n"
        
        # Duplicates
        result += "## 7. Duplicates\n\n"
        dup_count = df.duplicated().sum()
        result += f"- Duplicate rows: {dup_count} ({dup_count/len(df)*100:.2f}%)\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_profiler(self, args: dict) -> ToolResult:
        """Generate data profile."""
        import pandas as pd
        
        url = args["data_url"]
        minimal = args.get("minimal", True)
        
        df = pd.read_csv(url)
        
        try:
            from ydata_profiling import ProfileReport
            
            profile = ProfileReport(df, minimal=minimal, title="Data Profile")
            
            # Get JSON description
            description = profile.get_description()
            
            result = "# 📋 Data Profile Report\n\n"
            result += f"Generated using ydata-profiling\n\n"
            result += f"## Summary\n\n"
            result += f"- Variables: {description.table['n_var']}\n"
            result += f"- Observations: {description.table['n']}\n"
            result += f"- Missing cells: {description.table['n_cells_missing']}\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            # Fallback to basic profiling
            result = "# 📋 Basic Data Profile\n\n"
            result += "(Install ydata-profiling for full report)\n\n"
            
            result += f"## Shape\n{df.shape}\n\n"
            result += f"## Types\n```\n{df.dtypes.to_string()}\n```\n\n"
            result += f"## Stats\n```\n{df.describe().to_string()}\n```\n"
            
            return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_cleaner(self, args: dict) -> ToolResult:
        """Clean dataset."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        handle_missing = args.get("handle_missing", "none")
        handle_outliers = args.get("handle_outliers", "none")
        remove_duplicates = args.get("remove_duplicates", False)
        
        df = pd.read_csv(url)
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
    
    async def _handle_correlation(self, args: dict) -> ToolResult:
        """Compute correlation matrix."""
        import pandas as pd
        import numpy as np
        
        df = self._load_dataframe(args)
        method = args.get("method", "pearson")
        threshold = args.get("threshold", 0.0)
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
    
    async def _handle_statistical_test(self, args: dict) -> ToolResult:
        """Run statistical tests."""
        import pandas as pd
        import numpy as np
        from scipy import stats
        
        url = args["data_url"]
        test_type = args["test_type"]
        col1 = args.get("column1")
        col2 = args.get("column2")
        group_col = args.get("group_column")
        
        df = pd.read_csv(url)
        
        result = f"# 📊 Statistical Test: {test_type}\n\n"
        
        if test_type == "ttest" and col1 and col2:
            data1 = df[col1].dropna()
            data2 = df[col2].dropna()
            stat, pvalue = stats.ttest_ind(data1, data2)
            
            result += f"## T-Test: {col1} vs {col2}\n\n"
            result += f"- t-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "anova" and col1 and group_col:
            groups = [group[col1].dropna() for name, group in df.groupby(group_col)]
            stat, pvalue = stats.f_oneway(*groups)
            
            result += f"## ANOVA: {col1} by {group_col}\n\n"
            result += f"- F-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "chi2" and col1 and col2:
            contingency = pd.crosstab(df[col1], df[col2])
            stat, pvalue, dof, expected = stats.chi2_contingency(contingency)
            
            result += f"## Chi-Square: {col1} vs {col2}\n\n"
            result += f"- χ² statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Degrees of freedom: {dof}\n"
            result += f"- Significant at α=0.05: {'Yes' if pvalue < 0.05 else 'No'}\n"
            
        elif test_type == "normality" and col1:
            data = df[col1].dropna()
            stat, pvalue = stats.shapiro(data[:5000])  # Limit for large datasets
            
            result += f"## Normality Test (Shapiro-Wilk): {col1}\n\n"
            result += f"- W-statistic: {stat:.4f}\n"
            result += f"- p-value: {pvalue:.4f}\n"
            result += f"- Normal distribution: {'Yes' if pvalue > 0.05 else 'No'}\n"
        else:
            result += "Invalid test configuration. Check required parameters.\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_feature_engineer(self, args: dict) -> ToolResult:
        """Create derived features."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        operations = args.get("operations", [])
        
        df = pd.read_csv(url)
        
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


# Export tool functions
async def eda_auto_tool(args: dict) -> ToolResult:
    server = AnalyticsServer()
    return await server._handle_eda_auto(args)




async def data_cleaner_tool(args: dict) -> ToolResult:
    server = AnalyticsServer()
    return await server._handle_cleaner(args)

async def correlation_matrix_tool(args: dict) -> ToolResult:
    server = AnalyticsServer()
    return await server._handle_correlation(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = AnalyticsServer()
        await server.run()
        
    asyncio.run(main())
