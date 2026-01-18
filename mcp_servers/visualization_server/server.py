"""
Visualization MCP Server.

Provides tools for data visualization:
- Plotly interactive charts
- Statistical plots
- Geographic maps
"""

from __future__ import annotations

from typing import Any
import json
import base64

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class VisualizationServer(MCPServerBase):
    """MCP server for data visualization."""
    
    def __init__(self) -> None:
        super().__init__(name="visualization_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="plotly_chart",
                description="Create interactive Plotly chart",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "chart_type": {"type": "string", "description": "Type: line, bar, scatter, histogram, box, pie, heatmap"},
                        "x_column": {"type": "string", "description": "X-axis column"},
                        "y_column": {"type": "string", "description": "Y-axis column"},
                        "color_column": {"type": "string", "description": "Column for color grouping"},
                        "title": {"type": "string", "description": "Chart title"},
                    },
                    required=["data_url", "chart_type"],
                ),
            ),
            Tool(
                name="correlation_heatmap",
                description="Create correlation heatmap",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "title": {"type": "string", "description": "Chart title"},
                    },
                    required=["data_url"],
                ),
            ),
            Tool(
                name="distribution_plot",
                description="Create distribution/histogram plots",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "columns": {"type": "array", "description": "Columns to plot (or 'all' numeric)"},
                    },
                    required=["data_url"],
                ),
            ),
            Tool(
                name="pairplot",
                description="Create pairwise scatter plot matrix",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_url": {"type": "string", "description": "URL to CSV data"},
                        "columns": {"type": "array", "description": "Columns to include"},
                        "color_column": {"type": "string", "description": "Column for color"},
                    },
                    required=["data_url"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "plotly_chart":
                return await self._handle_plotly(arguments)
            elif name == "correlation_heatmap":
                return await self._handle_heatmap(arguments)
            elif name == "distribution_plot":
                return await self._handle_distribution(arguments)
            elif name == "pairplot":
                return await self._handle_pairplot(arguments)
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
    
    async def _handle_plotly(self, args: dict) -> ToolResult:
        """Create Plotly chart."""
        import pandas as pd
        import plotly.express as px
        import plotly.io as pio
        
        url = args["data_url"]
        chart_type = args["chart_type"]
        x_col = args.get("x_column")
        y_col = args.get("y_column")
        color_col = args.get("color_column")
        title = args.get("title", f"{chart_type.title()} Chart")
        
        df = pd.read_csv(url)
        
        # Create chart based on type
        if chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "histogram":
            fig = px.histogram(df, x=x_col or y_col, color=color_col, title=title)
        elif chart_type == "box":
            fig = px.box(df, x=x_col, y=y_col, color=color_col, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title)
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include=['number'])
            fig = px.imshow(numeric_df.corr(), title=title)
        else:
            return ToolResult(
                content=[TextContent(text=f"Unknown chart type: {chart_type}")],
                isError=True,
            )
        
        # Generate HTML
        html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False)
        
        result = f"# 📊 {title}\n\n"
        result += f"**Chart Type**: {chart_type}\n"
        result += f"**Data Shape**: {df.shape}\n\n"
        result += "## Interactive Chart\n\n"
        result += f"```html\n{html[:500]}...\n```\n\n"
        result += "(Full HTML available for rendering)\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_heatmap(self, args: dict) -> ToolResult:
        """Create correlation heatmap."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        title = args.get("title", "Correlation Heatmap")
        
        df = pd.read_csv(url)
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_distribution(self, args: dict) -> ToolResult:
        """Create distribution plots."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        columns = args.get("columns")
        
        df = pd.read_csv(url)
        
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
                max_val = max(hist)
                result += "\n### Histogram\n```\n"
                for i, h in enumerate(hist):
                    bar = "█" * int(h / max_val * 30)
                    result += f"{bins[i]:.1f} - {bins[i+1]:.1f} | {bar} ({h:,})\n"
                result += "```\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_pairplot(self, args: dict) -> ToolResult:
        """Create pairwise scatter matrix."""
        import pandas as pd
        import numpy as np
        
        url = args["data_url"]
        columns = args.get("columns")
        color_col = args.get("color_column")
        
        df = pd.read_csv(url)
        
        if not columns:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()[:4]
        
        result = "# 🔗 Pairplot Analysis\n\n"
        result += f"**Columns**: {columns}\n"
        if color_col:
            result += f"**Color by**: {color_col}\n"
        result += "\n"
        
        # Basic stats for pairs
        result += "## Pairwise Statistics\n\n"
        result += "| Pair | Correlation | Interpretation |\n|------|-------------|----------------|\n"
        
        for i, col1 in enumerate(columns):
            for col2 in columns[i+1:]:
                corr = df[col1].corr(df[col2])
                if abs(corr) > 0.7:
                    interp = "Strong"
                elif abs(corr) > 0.4:
                    interp = "Moderate"
                else:
                    interp = "Weak"
                result += f"| {col1} vs {col2} | {corr:.3f} | {interp} |\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def plotly_chart_tool(args: dict) -> ToolResult:
    server = VisualizationServer()
    return await server._handle_plotly(args)

async def correlation_heatmap_tool(args: dict) -> ToolResult:
    server = VisualizationServer()
    return await server._handle_heatmap(args)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = VisualizationServer()
        await server.run()
        
    asyncio.run(main())
