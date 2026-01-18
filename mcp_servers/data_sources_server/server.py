"""
Data Sources MCP Server.

Provides tools for fetching data from various sources:
- Financial: yfinance, FRED
- Census: World Bank, UN
- Commodities: USGS, EIA
"""

from __future__ import annotations

from typing import Any

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class DataSourcesServer(MCPServerBase):
    """MCP server for data source fetching."""
    
    def __init__(self) -> None:
        super().__init__(name="data_sources_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="yfinance_fetch",
                description="Fetch stock/financial data from Yahoo Finance",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "symbol": {"type": "string", "description": "Stock symbol (e.g. AAPL, MSFT)"},
                        "period": {"type": "string", "description": "Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"},
                        "interval": {"type": "string", "description": "Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo"},
                        "data_type": {"type": "string", "description": "Type: history, info, financials, balance_sheet, cashflow"},
                    },
                    required=["symbol"],
                ),
            ),
            Tool(
                name="fred_fetch",
                description="Fetch economic data from FRED (Federal Reserve Economic Data)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "series_id": {"type": "string", "description": "FRED series ID (e.g. GDP, UNRATE, CPIAUCSL)"},
                        "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    },
                    required=["series_id"],
                ),
            ),
            Tool(
                name="world_bank_fetch",
                description="Fetch development indicators from World Bank",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "indicator": {"type": "string", "description": "Indicator ID (e.g. NY.GDP.MKTP.CD for GDP)"},
                        "country": {"type": "string", "description": "Country code (e.g. US, ID, CN) or 'all'"},
                        "start_year": {"type": "integer", "description": "Start year"},
                        "end_year": {"type": "integer", "description": "End year"},
                    },
                    required=["indicator"],
                ),
            ),
            Tool(
                name="csv_fetch",
                description="Fetch CSV data from URL and return as DataFrame info",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to CSV file"},
                        "preview_rows": {"type": "integer", "description": "Number of rows to preview (default 5)"},
                    },
                    required=["url"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "yfinance_fetch":
                return await self._handle_yfinance(arguments)
            elif name == "fred_fetch":
                return await self._handle_fred(arguments)
            elif name == "world_bank_fetch":
                return await self._handle_world_bank(arguments)
            elif name == "csv_fetch":
                return await self._handle_csv_fetch(arguments)
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
    
    async def _handle_yfinance(self, args: dict) -> ToolResult:
        """Fetch data from Yahoo Finance."""
        import yfinance as yf
        
        symbol = args["symbol"]
        period = args.get("period", "1mo")
        interval = args.get("interval", "1d")
        data_type = args.get("data_type", "history")
        
        ticker = yf.Ticker(symbol)
        
        if data_type == "history":
            df = ticker.history(period=period, interval=interval)
            result = f"## {symbol} Price History\n\n"
            result += f"Period: {period}, Interval: {interval}\n"
            result += f"Rows: {len(df)}\n\n"
            result += "### Latest Data\n```\n"
            result += df.tail(10).to_string()
            result += "\n```\n"
            
        elif data_type == "info":
            info = ticker.info
            result = f"## {symbol} Company Info\n\n"
            key_fields = ['shortName', 'sector', 'industry', 'marketCap', 
                         'trailingPE', 'dividendYield', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']
            for field in key_fields:
                if field in info:
                    result += f"- **{field}**: {info[field]}\n"
                    
        elif data_type == "financials":
            df = ticker.financials
            result = f"## {symbol} Financials\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
            
        elif data_type == "balance_sheet":
            df = ticker.balance_sheet
            result = f"## {symbol} Balance Sheet\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
            
        elif data_type == "cashflow":
            df = ticker.cashflow
            result = f"## {symbol} Cash Flow\n\n```\n"
            result += df.to_string()
            result += "\n```\n"
        else:
            result = f"Unknown data_type: {data_type}"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_fred(self, args: dict) -> ToolResult:
        """Fetch data from FRED."""
        try:
            from fredapi import Fred
            import os
            
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                return ToolResult(
                    content=[TextContent(text="FRED_API_KEY not set")],
                    isError=True,
                )
            
            fred = Fred(api_key=api_key)
            
            series_id = args["series_id"]
            start = args.get("start_date")
            end = args.get("end_date")
            
            data = fred.get_series(series_id, observation_start=start, observation_end=end)
            
            result = f"## FRED: {series_id}\n\n"
            result += f"Observations: {len(data)}\n\n"
            result += "### Latest Values\n```\n"
            result += data.tail(20).to_string()
            result += "\n```\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            return ToolResult(
                content=[TextContent(text="fredapi not installed. Run: pip install fredapi")],
                isError=True,
            )
    
    async def _handle_world_bank(self, args: dict) -> ToolResult:
        """Fetch data from World Bank."""
        try:
            import wbgapi as wb
            
            indicator = args["indicator"]
            country = args.get("country", "all")
            start_year = args.get("start_year")
            end_year = args.get("end_year")
            
            time_range = None
            if start_year and end_year:
                time_range = range(start_year, end_year + 1)
            
            if country == "all":
                data = wb.data.DataFrame(indicator, time=time_range, labels=True)
            else:
                data = wb.data.DataFrame(indicator, economy=country, time=time_range, labels=True)
            
            result = f"## World Bank: {indicator}\n\n"
            result += f"Shape: {data.shape}\n\n"
            result += "### Data\n```\n"
            result += data.head(20).to_string()
            result += "\n```\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            return ToolResult(
                content=[TextContent(text="wbgapi not installed. Run: pip install wbgapi")],
                isError=True,
            )
    
    async def _handle_csv_fetch(self, args: dict) -> ToolResult:
        """Fetch CSV from URL."""
        import pandas as pd
        
        url = args["url"]
        preview_rows = args.get("preview_rows", 5)
        
        df = pd.read_csv(url)
        
        result = f"## CSV Data from URL\n\n"
        result += f"**URL**: {url}\n\n"
        result += f"**Shape**: {df.shape[0]} rows × {df.shape[1]} columns\n\n"
        
        result += "### Columns\n"
        for col in df.columns:
            dtype = df[col].dtype
            nulls = df[col].isnull().sum()
            result += f"- `{col}` ({dtype}) - {nulls} nulls\n"
        
        result += f"\n### Preview (first {preview_rows} rows)\n```\n"
        result += df.head(preview_rows).to_string()
        result += "\n```\n"
        
        result += "\n### Statistics\n```\n"
        result += df.describe().to_string()
        result += "\n```\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions for direct use
async def yfinance_fetch_tool(args: dict) -> ToolResult:
    server = DataSourcesServer()
    return await server._handle_yfinance(args)

async def fred_fetch_tool(args: dict) -> ToolResult:
    server = DataSourcesServer()
    return await server._handle_fred(args)

async def world_bank_fetch_tool(args: dict) -> ToolResult:
    server = DataSourcesServer()
    return await server._handle_world_bank(args)

async def csv_fetch_tool(args: dict) -> ToolResult:
    server = DataSourcesServer()
    return await server._handle_csv_fetch(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = DataSourcesServer()
        await server.run()
        
    asyncio.run(main())



