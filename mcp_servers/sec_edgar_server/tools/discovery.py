
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import os

async def scan_local_library(arguments: dict) -> ToolResult:
    """
    Scan the SEC_DATA_DIR to inventory all downloaded filings.
    Returns: Ticker breakdown.
    """
    try:
        base_dir = os.path.join(SecCore.get_downloader().download_folder, "sec-edgar-filings")
        if not os.path.exists(base_dir):
            return dict_to_result({"total_tickers": 0}, "Empty Library")
            
        tickers = os.listdir(base_dir)
        inventory = {}
        total_files = 0
        
        for t in tickers:
            t_path = os.path.join(base_dir, t)
            if os.path.isdir(t_path):
                inventory[t] = {}
                # Walk types
                types = os.listdir(t_path)
                for f_type in types:
                    type_path = os.path.join(t_path, f_type)
                    if os.path.isdir(type_path):
                        # Count accessions (folders)
                        accessions = os.listdir(type_path)
                        count = len(accessions)
                        inventory[t][f_type] = count
                        total_files += count
                        
        return dict_to_result({
            "total_tickers": len(inventory),
            "total_filings": total_files,
            "inventory": inventory,
            "storage_path": base_dir
        }, "Local Library Inventory")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
