
from openpyxl import load_workbook
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import os
import json

logger = get_logger(__name__)

def dict_to_result(data: dict) -> ToolResult:
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])

def _get_wb(path, read_only=False, keep_vba=True):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return load_workbook(path, read_only=read_only, keep_vba=keep_vba)

async def check_vba_project(arguments: dict) -> ToolResult:
    """Check if workbook has VBA macros."""
    try:
        path = arguments['file_path']
        # Must load with keep_vba=True to detect
        wb = _get_wb(path, read_only=True, keep_vba=True)
        
        has_vba = False
        try:
             # vba_archive implies visibility
             if wb.vba_archive: has_vba = True
        except:
             pass
             
        # Also file extension check hint
        ext = os.path.splitext(path)[1].lower()
        
        wb.close()
        return dict_to_result({"has_vba": has_vba, "extension": ext, "status": "checked"})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def set_custom_property(arguments: dict) -> ToolResult:
    """Add a custom document property."""
    try:
        path = arguments['file_path']
        name = arguments['name']
        value = arguments['value'] # str, int, float, bool, date
        type_ = arguments.get('type', 'text') # text, number, date, bool
        
        wb = _get_wb(path)
        
        # OpenPyXL handles props via wb.custom_doc_props
        # But setting them requires specific API or manual XML assignment in older versions?
        # Newer versions:
        props = wb.custom_doc_props
        props.append(name=name, value=value, type=type_)
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "property_added", "name": name, "value": value})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
