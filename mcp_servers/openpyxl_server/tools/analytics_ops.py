
from openpyxl import load_workbook
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import os
import json

logger = get_logger(__name__)

def dict_to_result(data: dict) -> ToolResult:
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])

def _get_wb(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return load_workbook(path)

async def create_pivot_table(arguments: dict) -> ToolResult:
    """
    Create a Pivot Table.
    Note: OpenPyXL support for Pivot Tables is limited to creating definitions.
    It does NOT calculate the pivot data. You must open in Excel to refresh.
    WARNING: Complex. Requires naming range or explicit cache.
    """
    return ToolResult(content=[TextContent(text="Feature partially implemented: OpenPyXL can create Pivot Table definitions but cannot calculate them. This tool is reserved for future implementation.")])
