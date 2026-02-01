
from edgar import set_identity, Company, get_filings
from shared.mcp.protocol import ToolResult, TextContent
import json

# Initialize Identity Globally
# Real usage requires valid email.
set_identity("Kea Agent <kea@antigravity.dev>")

def dict_to_result(data: dict, title: str = "Result") -> ToolResult:
    # Custom serializer for edgar objects might be needed, but they usually have .to_dict() or we extract fields
    def default(o):
        if hasattr(o, 'to_dict'): return o.to_dict()
        return str(o)
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=default))])

class EdgarCore:
    @staticmethod
    def get_company(ticker: str) -> Company:
        c = Company(ticker)
        # Check for dummy CIK returned by library for invalid tickers
        if hasattr(c, 'cik') and (str(c.cik) == "-999999999" or c.cik == -999999999):
            raise ValueError(f"Company {ticker} not found in EDGAR database.")
        return c
