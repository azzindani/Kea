
from sec_edgar_downloader import Downloader
from shared.mcp.protocol import ToolResult, TextContent
import os
import shutil

# Central Storage
SEC_DATA_DIR = r"D:\Antigravity\Kea\sec_data"

class SecCore:
    _instance = None
    
    @staticmethod
    def get_downloader() -> Downloader:
        # UserAgent required: "Name <Email>"
        # Using a generic one for the Agent. User should ideally configure this.
        # But for 'works out of the box', we use a placeholder.
        # "Kea Agent <kea@antigravity.dev>"
        return Downloader("Kea Agent", "kea@antigravity.dev", SEC_DATA_DIR)

    @staticmethod
    def get_download_path(ticker: str, filing_type: str) -> str:
        return os.path.join(SEC_DATA_DIR, "sec-edgar-filings", ticker, filing_type)

def dict_to_result(data: dict, title: str = "Result") -> ToolResult:
    import json
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])
