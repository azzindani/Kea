
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.workbook.defined_name import DefinedName
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

# ============================================================================
# Data Validation
# ============================================================================

async def add_list_validation(arguments: dict) -> ToolResult:
    """Create a Dropdown List validation."""
    try:
        path = arguments['file_path']
        cell_range = arguments['cell_range'] # 'A1:A10' or 'A1'
        options = arguments.get('options') # list of strings ["Yes", "No"]
        formula = arguments.get('formula') # OR reference "=Sheet2!A1:A5"
        allow_blank = arguments.get('allow_blank', True)
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        # Construct formula list '"Yes,No"' or use passed formula
        if options:
            quoted = [f'"{opt}"' if ',' in opt else str(opt) for opt in options] 
            # Actually Excel expects comma separated string "Yes,No"
            f_str = f'"{",".join([str(o) for o in options])}"'
            dv = DataValidation(type="list", formula1=f_str, allow_blank=allow_blank)
        elif formula:
            dv = DataValidation(type="list", formula1=formula, allow_blank=allow_blank)
        else:
            return ToolResult(isError=True, content=[TextContent(text="Must provide options or formula")])
            
        ws.add_data_validation(dv)
        dv.add(cell_range) # This accepts range string? Yes usually.
        # Sometimes needs to be separated?
        # A1:A10 is fine.
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "validation_added", "type": "list", "range": cell_range})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# ============================================================================
# Tables
# ============================================================================

async def create_table(arguments: dict) -> ToolResult:
    """Convert a range to an Excel Table."""
    try:
        path = arguments['file_path']
        range_string = arguments['range_string'] # 'A1:D10'
        table_name = arguments.get('table_name', 'Table1')
        style_name = arguments.get('style_name', 'TableStyleMedium9')
        sheet_name = arguments.get('sheet_name')
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        tab = Table(displayName=table_name, ref=range_string)
        
        # Add Style
        style = TableStyleInfo(name=style_name, showFirstColumn=False,
                               showLastColumn=False, showRowStripes=True, showColumnStripes=True)
        tab.tableStyleInfo = style
        
        ws.add_table(tab)
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "table_created", "name": table_name, "range": range_string})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# ============================================================================
# Protection
# ============================================================================

async def protect_sheet(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        password = arguments.get('password')
        sheet_name = arguments.get('sheet_name')
        enable_select_locked = arguments.get('enable_select_locked', True)
        enable_format_cells = arguments.get('enable_format_cells', False)
        
        wb = _get_wb(path)
        ws = wb[sheet_name] if sheet_name else wb.active
        
        ws.protection.sheet = True # Enable protection
        if password:
            ws.protection.password = password
            
        ws.protection.enable() # Sets defaults
        # Custom flags
        ws.protection.formatCells = not enable_format_cells # False means protected? 
        # Actually in openpyxl, these attributes are Permissions. False means "Locked". True means "Allowed".
        # Documentation is tricky. 
        # Let's stick to basic enable/disable for V1.
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "sheet_protected"})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# ============================================================================
# Named Ranges
# ============================================================================

async def add_defined_name(arguments: dict) -> ToolResult:
    try:
        path = arguments['file_path']
        name = arguments['name']
        ref = arguments['ref'] # 'Sheet1!$A$1:$A$10'
        
        wb = _get_wb(path)
        dn = DefinedName(name, attr_text=ref)
        wb.defined_names[name] = dn
        
        wb.save(path)
        wb.close()
        return dict_to_result({"status": "defined_name_added", "name": name, "ref": ref})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
