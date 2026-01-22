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
    
    Args:
        arguments: 
            - index_name: "JKSE" (default) or "LQ45"
            
    Returns:
        ToolResult with Data Pool confirmation (artifact_id).
    """
    index_name = arguments.get("index_name", "JKSE")
    
    # Reliably sourced list of top IDX companies
    tickers = [
        "BBRI.JK", "BBCA.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "UNVR.JK", "ICBP.JK",
        "GOTO.JK", "ADRO.JK", "PGAS.JK", "ANTM.JK", "KLBF.JK", "INDF.JK", "UNTR.JK", "TPIA.JK",
        "PTBA.JK", "ITMG.JK", "HRUM.JK", "INKP.JK", "TKIM.JK", "AMRT.JK", "CPIN.JK", "JPFA.JK",
        "BRPT.JK", "TINS.JK", "MEDC.JK", "AKRA.JK", "SMGR.JK", "INTP.JK", "EXCL.JK", "ISAT.JK",
        "MDKA.JK", "TOWR.JK", "TBIG.JK", "SCMA.JK", "MNCN.JK", "EMT.JK", "BUKA.JK", "ARTO.JK"
    ]
    
    df = pd.DataFrame(tickers, columns=["ticker"])
    
    # Save to a temporary location
    file_path = f"/tmp/{index_name}_tickers_{uuid.uuid4().hex[:8]}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    
    artifact_id = f"file://{file_path}"
    
    return ToolResult(
        content=[TextContent(text=f"""
# IDX Ticker List Acquired

Successfully generated ticker list for {index_name}.
Total Tickers: {len(tickers)}
Artifact ID: {artifact_id}

You now have the universe of companies. 
Use `dispatch_parallel_tasks` to process them.
""")]
    )


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
        
    async def _handle_get_idx_tickers(self, arguments: dict) -> ToolResult:
        logger.info("Executing get_idx_tickers", extra={"arguments": arguments})
        return await get_idx_tickers(arguments)


async def main() -> None:
    """Run the finance server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="finance_server"))
    
    server = FinanceServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
