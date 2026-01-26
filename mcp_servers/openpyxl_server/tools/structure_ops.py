
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

# ============================================================================
# Outlining (Grouping)
# ============================================================================

async def group_rows(arguments: dict) -> ToolResult:
    """Group rows (create outline level)."""
    try:
        path = arguments['file_path']
        start_row = arguments['start_row'] # int
        end_row = arguments['end_row']     # int
        level = arguments.get('level', 1)  # 1-based usually
        hidden = arguments.get('hidden', False)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        # openpyxl uses row_dimensions.outlineLevel
        # And we set 'hidden' if needed.
        for row in range(start_row, end_row + 1):
            ws.row_dimensions[row].outlineLevel = level
            ws.row_dimensions[row].hidden = hidden
            
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "rows_grouped", "start": start_row, "end": end_row, "level": level})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def ungroup_rows(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        start_row = arguments['start_row']
        end_row = arguments['end_row']
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        for row in range(start_row, end_row + 1):
            ws.row_dimensions[row].outlineLevel = 0 # 0 is no group
            ws.row_dimensions[row].hidden = False
            
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "rows_ungrouped", "start": start_row, "end": end_row})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def group_cols(arguments: dict) -> ToolResult:
    """Group columns (by column string 'A', 'B' or index?). OpenPyXL usually prefers string for cols."""
    try:
        path = arguments['file_path']
        start_col = arguments['start_col'] # 'A'
        end_col = arguments['end_col']     # 'C'
        level = arguments.get('level', 1)
        hidden = arguments.get('hidden', False)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        ws.column_dimensions.group(start_col, end_col, outline_level=level, hidden=hidden)
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "cols_grouped", "start": start_col, "end": end_col})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# ============================================================================
# Window / View
# ============================================================================

async def freeze_panes(arguments: dict) -> ToolResult:
    """Freeze panes at a cell (e.g. 'B2' freezes row 1 and col A)."""
    try:
        path = arguments['file_path']
        cell = arguments['cell'] # 'A2' for top row, 'B1' for left col, 'B2' for both
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        ws.freeze_panes = cell
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "panes_frozen", "cell": cell})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def set_zoom_scale(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        zoom = arguments['zoom'] # int, e.g. 85
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        ws.sheet_view.zoomScale = zoom
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "zoom_set", "zoom": zoom})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
