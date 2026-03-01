
from openpyxl import load_workbook
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
import os
import json

logger = get_logger(__name__)

def dict_to_result(data: dict) -> ToolResult:
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])

def _get_wb(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return load_workbook(path)

async def insert_rows(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        idx = arguments['idx'] # 1-based Row index
        amount = arguments.get('amount', 1)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        ws.insert_rows(idx, amount)
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "rows_inserted", "idx": idx, "amount": amount})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def delete_rows(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        idx = arguments['idx']
        amount = arguments.get('amount', 1)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        ws.delete_rows(idx, amount)
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "rows_deleted", "idx": idx, "amount": amount})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def insert_cols(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        idx = arguments['idx'] # 1-based Column index (int)
        amount = arguments.get('amount', 1)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        ws.insert_cols(idx, amount)
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "cols_inserted", "idx": idx, "amount": amount})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def delete_cols(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        idx = arguments['idx']
        amount = arguments.get('amount', 1)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        ws.delete_cols(idx, amount)
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "cols_deleted", "idx": idx, "amount": amount})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def move_range(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        range_string = arguments['range_string']
        rows = arguments.get('rows', 0)
        cols = arguments.get('cols', 0)
        translate = arguments.get('translate', True) # Update formulas
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        ws.move_range(range_string, rows=rows, cols=cols, translate=translate)
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "moved", "range": range_string, "rows": rows, "cols": cols})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
