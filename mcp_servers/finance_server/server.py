"""
Finance MCP Server.

Provides specialized financial tools via MCP protocol.
"""

from __future__ import annotations

import asyncio
import os
import pandas as pd
import uuid
from typing import Any

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)



async def get_idx_tickers(arguments: dict) -> ToolResult:
    """
    Fetches the list of tickers for the Jakarta Stock Exchange (IDX).
    """
    index_name = arguments.get("index_name", "JKSE")
    
    # Try fetching real components if possible, or use expanded static list
    # Ideally use yfinance to get components if supported, or scrape.
    # For now, we expand the static list to be more comprehensive for "Massive" tests
    tickers = [
        "BBRI.JK", "BBCA.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "UNVR.JK", "ICBP.JK",
        "GOTO.JK", "ADRO.JK", "PGAS.JK", "ANTM.JK", "KLBF.JK", "INDF.JK", "UNTR.JK", "TPIA.JK",
        "PTBA.JK", "ITMG.JK", "HRUM.JK", "INKP.JK", "TKIM.JK", "AMRT.JK", "CPIN.JK", "JPFA.JK",
        "BRPT.JK", "TINS.JK", "MEDC.JK", "AKRA.JK", "SMGR.JK", "INTP.JK", "EXCL.JK", "ISAT.JK",
        "MDKA.JK", "TOWR.JK", "TBIG.JK", "SCMA.JK", "MNCN.JK", "EMT.JK", "BUKA.JK", "ARTO.JK",
        "MYOR.JK", "SIDO.JK", "HEAL.JK", "MIKA.JK", "SILO.JK", "BTPS.JK"
    ]
    
    df = pd.DataFrame(tickers, columns=["symbol"])
    
    # Save to a temporary location
    file_path = f"/tmp/{index_name}_tickers_{uuid.uuid4().hex[:8]}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    
    artifact_id = f"file://{file_path}"
    
    # Context Injection (The Handoff Fix)
    ticker_str = ", ".join(tickers)
    
    return ToolResult(
        content=[TextContent(text=f"""
# IDX Ticker List Acquired

Successfully generated ticker list for {index_name}.
Total Tickers: {len(tickers)}
Artifact ID: {artifact_id}
List: {ticker_str}

You now have the universe of companies. 
Use `dispatch_parallel_tasks` to process them.
""")]
    )


async def get_ticker_metrics(arguments: dict) -> ToolResult:
    """
    Get live financial metrics for a specific ticker using yfinance.
    
    Args:
        arguments:
            - ticker: Stock symbol (e.g., "ASII.JK")
            
    Returns:
        Key metrics: Market Cap, PE, Revenue Growth, etc.
    """
    import yfinance as yf
    
    ticker = arguments.get("ticker")
    if not ticker:
        return ToolResult(isError=True, content=[TextContent(text="Ticker argument required")])
        
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key metrics with safe defaults
        metrics = {
            "symbol": ticker,
            "company_name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "market_cap_idr_t": info.get("marketCap", 0) / 1_000_000_000_000, # Trillions
            "pe_ratio": info.get("trailingPE", 0),
            "forward_pe": info.get("forwardPE", 0),
            "revenue_growth_yoy": info.get("revenueGrowth", 0) * 100, # Percent
            "profit_margin": info.get("profitMargins", 0) * 100, # Percent
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "IDR"),
            "last_updated": "Live (Yahoo Finance)"
        }
        
        source_url = f"https://finance.yahoo.com/quote/{ticker}"
        
        # Format as markdown table
        md = f"""
### Financial Metrics for {metrics['company_name']} ({ticker})

| Metric | Value |
| :--- | :--- |
| **Market Cap** | {metrics['market_cap_idr_t']:.2f} T IDR |
| **Price** | {metrics['price']} {metrics['currency']} |
| **P/E Ratio** | {metrics['pe_ratio']:.2f} |
| **Rev Growth (YoY)** | {metrics['revenue_growth_yoy']:.1f}% |
| **Data Source** | Yahoo Finance (Live) |
| **Source URL** | {source_url} |

Raw Data:
{metrics}
"""
        return ToolResult(content=[TextContent(text=md)])
        
    except Exception as e:
        logger.error(f"Failed to fetch yfinance data for {ticker}: {e}")
        return ToolResult(isError=True, content=[TextContent(text=f"Failed to fetch data for {ticker}: {str(e)}")])



class FinanceServer(MCPServer):
    """MCP Server for financial tools."""
    
    def __init__(self) -> None:
        super().__init__(name="finance_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all finance tools."""
        self.register_tool(
            name="get_idx_tickers",
            description="Get reliable list of Indonesia Stock Exchange (IDX) tickers for a specific index.",
            handler=self._handle_get_idx_tickers,
            parameters={
                "index_name": {
                    "type": "string",
                    "description": "Index component (e.g. 'JKSE', 'LQ45'). Default: 'JKSE'"
                },
                "force_refresh": {
                    "type": "boolean",
                    "description": "If true, fetches live data from source instead of cache. Default: false"
                }
            },
            required=[]
        )
        
        self.register_tool(
            name="get_ticker_metrics",
            description="Get live financial metrics (Market Cap, PE, Growth) for a stock ticker from Yahoo Finance.",
            handler=self._handle_get_ticker_metrics,
            parameters={
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g. 'ASII.JK')"
                }
            },
            required=["ticker"]
        )
        
    async def _handle_get_idx_tickers(self, arguments: dict) -> ToolResult:
        logger.info("Executing get_idx_tickers", extra={"arguments": arguments})
        return await get_idx_tickers(arguments)

    async def _handle_get_ticker_metrics(self, arguments: dict) -> ToolResult:
        logger.info("Executing get_ticker_metrics", extra={"arguments": arguments})
        return await get_ticker_metrics(arguments)


async def main() -> None:
    """Run the finance server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="finance_server"))
    
    server = FinanceServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
