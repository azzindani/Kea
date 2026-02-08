
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "openpyxl",
#   "pandas",
#   "pillow",
#   "structlog",
# ]
# ///


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.openpyxl_server.tools import (
    workbook_ops, sheet_ops, read_ops, write_ops, manage_rows_cols,
    style_ops, chart_ops, object_ops, formatting_ops, advanced_features,
    structure_ops, analytics_ops, formula_ops, metadata_ops, clean_ops,
    audit_ops, template_ops
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("openpyxl_server", dependencies=["openpyxl", "pandas", "pillow"])

async def run_op(op_func, **kwargs):
    """Helper to run legacy tool ops that expect a dict and return ToolResult."""
    try:
        # Filter out None values to match legacy behavior where missing args weren't in dict
        # Actually legacy relies on .get(), so passing everything is fine.
        # But we need to ensure arguments match what the tool expects.
        # The tools expect a single 'arguments' dict.
        result = await op_func(kwargs)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
        
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# 1. Multitalent / Super Tools
# 1. Multitalent / Super Tools
@mcp.tool()
async def analyze_workbook_file(file_path: str) -> str:
    """ANALYZES workbook. [ACTION]
    
    [RAG Context]
    Inspect structure, sheets, ranges, and stats of Excel file.
    Returns text report.
    """
    return await run_op(workbook_ops.analyze_workbook_file, file_path=file_path)

# 2. Workbook
@mcp.tool()
async def create_new_workbook(file_path: str, overwrite: bool = False) -> str:
    """CREATES workbook. [ACTION]
    
    [RAG Context]
    Create a new empty .xlsx file.
    Returns status string.
    """
    return await run_op(workbook_ops.create_new_workbook, file_path=file_path, overwrite=overwrite)

@mcp.tool()
async def get_workbook_metadata(file_path: str) -> str:
    """FETCHES meta. [ACTION]
    
    [RAG Context]
    Get metadata (author, created, modified) from workbook.
    Returns JSON string.
    """
    return await run_op(workbook_ops.get_workbook_metadata, file_path=file_path)

@mcp.tool()
async def list_named_ranges(file_path: str) -> str:
    """LISTS named ranges. [ACTION]
    
    [RAG Context]
    Get all defined names/ranges in workbook.
    Returns table string.
    """
    return await run_op(workbook_ops.list_named_ranges, file_path=file_path)

# 3. Sheet Ops
@mcp.tool()
async def list_worksheets(file_path: str) -> str:
    """LISTS worksheets. [ACTION]
    
    [RAG Context]
    Get list of sheet names in workbook.
    Returns list string.
    """
    return await run_op(sheet_ops.list_worksheets, file_path=file_path)

@mcp.tool()
async def create_worksheet(file_path: str, title: str, index: int = None) -> str:
    """CREATES worksheet. [ACTION]
    
    [RAG Context]
    Add a new sheet to the workbook.
    Returns status string.
    """
    return await run_op(sheet_ops.create_worksheet, file_path=file_path, title=title, index=index)

@mcp.tool()
async def delete_worksheet(file_path: str, sheet_name: str) -> str:
    """DELETES worksheet. [ACTION]
    
    [RAG Context]
    Remove a sheet from the workbook.
    Returns status string.
    """
    return await run_op(sheet_ops.delete_worksheet, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def rename_worksheet(file_path: str, old_name: str, new_name: str) -> str:
    """RENAMES worksheet. [ACTION]
    
    [RAG Context]
    Change the name of an existing sheet.
    Returns status string.
    """
    return await run_op(sheet_ops.rename_worksheet, file_path=file_path, old_name=old_name, new_name=new_name)

@mcp.tool()
async def copy_worksheet(file_path: str, source_sheet: str, new_title: str) -> str:
    """COPIES worksheet. [ACTION]
    
    [RAG Context]
    Duplicate an existing sheet.
    Returns status string.
    """
    return await run_op(sheet_ops.copy_worksheet, file_path=file_path, source_sheet=source_sheet, new_title=new_title)

@mcp.tool()
async def get_sheet_properties(file_path: str, sheet_name: str) -> str:
    """FETCHES sheet props. [ACTION]
    
    [RAG Context]
    Get sheet attributes (tab color, hidden state).
    Returns JSON string.
    """
    return await run_op(sheet_ops.get_sheet_properties, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def set_sheet_properties(file_path: str, sheet_name: str, tab_color: str = None, state: str = None) -> str:
    """SETS sheet props. [ACTION]
    
    [RAG Context]
    Set tab color or visibility state.
    Returns status string.
    """
    return await run_op(sheet_ops.set_sheet_properties, file_path=file_path, sheet_name=sheet_name, tab_color=tab_color, state=state)

# 4. Reading
# 4. Reading
@mcp.tool()
async def read_excel_multitalent(file_path: str, sheet_name: str = None, range_string: str = None, header_row: int = 1) -> str:
    """READS Excel (Bulk). [ACTION]
    
    [RAG Context]
    Flexible reader for sheets, ranges, or tables.
    Returns table string (markdown).
    """
    return await run_op(read_ops.read_excel_multitalent, file_path=file_path, sheet_name=sheet_name, range_string=range_string, header_row=header_row)

@mcp.tool()
async def read_cell_value(file_path: str, cell: str, sheet_name: str = None) -> str:
    """READS cell. [ACTION]
    
    [RAG Context]
    Get value of a single cell (e.g., 'A1').
    Returns value string.
    """
    return await run_op(read_ops.read_cell_value, file_path=file_path, cell=cell, sheet_name=sheet_name)

@mcp.tool()
async def search_excel_content(file_path: str, query: str, is_regex: bool = False) -> str:
    """SEARCHES content. [ACTION]
    
    [RAG Context]
    Find cells containing text or matching regex.
    Returns list of matches.
    """
    return await run_op(read_ops.search_excel_content, file_path=file_path, query=query, is_regex=is_regex)

@mcp.tool()
async def read_range_values(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """READS range values. [ACTION]
    
    [RAG Context]
    Get values from a specific range (e.g., 'A1:B10').
    Returns JSON string (list of lists).
    """
    return await run_op(read_ops.read_range_values, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 5. Writing
# 5. Writing
@mcp.tool()
async def write_cell_value(file_path: str, cell: str, value: str, sheet_name: str = None) -> str:
    """WRITES cell. [ACTION]
    
    [RAG Context]
    Set value of a single cell.
    Returns status string.
    """
    return await run_op(write_ops.write_cell_value, file_path=file_path, cell=cell, value=value, sheet_name=sheet_name)

@mcp.tool()
async def write_range_values(file_path: str, data: list, start_cell: str = "A1", sheet_name: str = None) -> str:
    """WRITES range. [ACTION]
    
    [RAG Context]
    Write 2D list of data starting at cell.
    Returns status string.
    """
    return await run_op(write_ops.write_range_values, file_path=file_path, data=data, start_cell=start_cell, sheet_name=sheet_name)

@mcp.tool()
async def write_formula(file_path: str, cell: str, formula: str, sheet_name: str = None) -> str:
    """WRITES formula. [ACTION]
    
    [RAG Context]
    Set cell formula (e.g., '=SUM(A1:A10)').
    Returns status string.
    """
    return await run_op(write_ops.write_formula, file_path=file_path, cell=cell, formula=formula, sheet_name=sheet_name)

@mcp.tool()
async def clear_range(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """CLEARS range. [ACTION]
    
    [RAG Context]
    Clear content/values from a range.
    Returns status string.
    """
    return await run_op(write_ops.clear_range, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 6. Struct Editing
# 6. Struct Editing
@mcp.tool()
async def insert_rows(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """INSERTS rows. [ACTION]
    
    [RAG Context]
    Insert empty rows at index.
    Returns status string.
    """
    return await run_op(manage_rows_cols.insert_rows, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def delete_rows(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """DELETES rows. [ACTION]
    
    [RAG Context]
    Delete rows at index.
    Returns status string.
    """
    return await run_op(manage_rows_cols.delete_rows, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def insert_cols(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """INSERTS cols. [ACTION]
    
    [RAG Context]
    Insert empty columns at index.
    Returns status string.
    """
    return await run_op(manage_rows_cols.insert_cols, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def delete_cols(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """DELETES cols. [ACTION]
    
    [RAG Context]
    Delete columns at index.
    Returns status string.
    """
    return await run_op(manage_rows_cols.delete_cols, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def move_range(file_path: str, range_string: str, rows: int, cols: int, sheet_name: str = None) -> str:
    """MOVES range. [ACTION]
    
    [RAG Context]
    Shift range of cells by rows/cols offset.
    Returns status string.
    """
    return await run_op(manage_rows_cols.move_range, file_path=file_path, range_string=range_string, rows=rows, cols=cols, sheet_name=sheet_name)

# 7. Styling
@mcp.tool()
async def set_cell_font(file_path: str, cell: str, font_name: str = None, size: float = None, bold: bool = None, color: str = None) -> str:
    """SETS cell font. [ACTION]
    
    [RAG Context]
    Change font, size, bold, or color of a cell.
    Returns status string.
    """
    return await run_op(style_ops.set_cell_font, file_path=file_path, cell=cell, font_name=font_name, size=size, bold=bold, color=color)

@mcp.tool()
async def set_cell_fill(file_path: str, cell: str, color: str, sheet_name: str = None) -> str:
    """SETS cell fill. [ACTION]
    
    [RAG Context]
    Set cell background color (hex code).
    Returns status string.
    """
    return await run_op(style_ops.set_cell_fill, file_path=file_path, cell=cell, color=color, sheet_name=sheet_name)

@mcp.tool()
async def set_cell_border(file_path: str, cell: str, style: str = "thin", color: str = "000000") -> str:
    """SETS cell border. [ACTION]
    
    [RAG Context]
    Apply border style to a cell.
    Returns status string.
    """
    return await run_op(style_ops.set_cell_border, file_path=file_path, cell=cell, style=style, color=color)

@mcp.tool()
async def merge_cells(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """MERGES cells. [ACTION]
    
    [RAG Context]
    Merge a range of cells into one.
    Returns status string.
    """
    return await run_op(style_ops.merge_cells, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

@mcp.tool()
async def unmerge_cells(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """UNMERGES cells. [ACTION]
    
    [RAG Context]
    Unmerge a previously merged range.
    Returns status string.
    """
    return await run_op(style_ops.unmerge_cells, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 8. Advanced (Charts/Objects)
# 8. Advanced (Charts/Objects)
@mcp.tool()
async def create_chart(file_path: str, type: str, data_range: str, title: str = None, anchor: str = "E5") -> str:
    """CREATES chart. [ACTION]
    
    [RAG Context]
    Add a chart (bar, line, pie) to the sheet.
    Returns status string.
    """
    return await run_op(chart_ops.create_chart, file_path=file_path, type=type, data_range=data_range, title=title, anchor=anchor)

@mcp.tool()
async def add_image_to_sheet(file_path: str, image_path: str, anchor: str = "A1") -> str:
    """INSERTS image. [ACTION]
    
    [RAG Context]
    Embed an image file into the sheet.
    Returns status string.
    """
    return await run_op(object_ops.add_image_to_sheet, file_path=file_path, image_path=image_path, anchor=anchor)

@mcp.tool()
async def add_comment(file_path: str, cell: str, text: str, author: str = "AI") -> str:
    """ADDS comment. [ACTION]
    
    [RAG Context]
    Add a comment to a specific cell.
    Returns status string.
    """
    return await run_op(object_ops.add_comment, file_path=file_path, cell=cell, text=text, author=author)

@mcp.tool()
async def read_comments(file_path: str, sheet_name: str = None) -> str:
    """READS comments. [ACTION]
    
    [RAG Context]
    Get all comments in a sheet.
    Returns list string.
    """
    return await run_op(object_ops.read_comments, file_path=file_path, sheet_name=sheet_name)

# 9. Formatting
@mcp.tool()
async def add_color_scale(file_path: str, range_string: str, start_color: str = "F8696B", mid_color: str = "FFEB84", end_color: str = "63BE7B") -> str:
    """APPLIES color scale. [ACTION]
    
    [RAG Context]
    Add Color Scale conditional formatting.
    Returns status string.
    """
    return await run_op(formatting_ops.add_color_scale, file_path=file_path, range_string=range_string, start_color=start_color, mid_color=mid_color, end_color=end_color)

@mcp.tool()
async def add_data_bar(file_path: str, range_string: str, color: str = "638EC6") -> str:
    """APPLIES data bar. [ACTION]
    
    [RAG Context]
    Add Data Bar conditional formatting.
    Returns status string.
    """
    return await run_op(formatting_ops.add_data_bar, file_path=file_path, range_string=range_string, color=color)

@mcp.tool()
async def add_highlight_rule(file_path: str, range_string: str, operator: str, formula: list = None, fill_color: str = "FFC7CE", font_color: str = "9C0006", bold: bool = False) -> str:
    """APPLIES highlight rule. [ACTION]
    
    [RAG Context]
    Add conditional formatting based on rule.
    Returns status string.
    """
    return await run_op(formatting_ops.add_highlight_rule, file_path=file_path, range_string=range_string, operator=operator, formula=formula, fill_color=fill_color, font_color=font_color, bold=bold)

@mcp.tool()
async def set_page_setup(file_path: str, orientation: str = None, paper_size: int = None, fit_to_width: int = None, fit_to_height: int = None) -> str:
    """SETS page setup. [ACTION]
    
    [RAG Context]
    Configure print settings (orientation, size).
    Returns status string.
    """
    return await run_op(formatting_ops.set_page_setup, file_path=file_path, orientation=orientation, paper_size=paper_size, fit_to_width=fit_to_width, fit_to_height=fit_to_height)

@mcp.tool()
async def set_print_area(file_path: str, print_area: str) -> str:
    """SETS print area. [ACTION]
    
    [RAG Context]
    Define the range to be printed.
    Returns status string.
    """
    return await run_op(formatting_ops.set_print_area, file_path=file_path, print_area=print_area)

# 10. Advanced Features
# 10. Advanced Features
@mcp.tool()
async def add_list_validation(file_path: str, cell_range: str, options: list = None, formula: str = None) -> str:
    """ADDS dropdown. [ACTION]
    
    [RAG Context]
    Add data validation (dropdown list) to cells.
    Returns status string.
    """
    return await run_op(advanced_features.add_list_validation, file_path=file_path, cell_range=cell_range, options=options, formula=formula)

@mcp.tool()
async def create_table(file_path: str, range_string: str, table_name: str = None, style_name: str = "TableStyleMedium9") -> str:
    """CREATES table. [ACTION]
    
    [RAG Context]
    Format range as an Excel table.
    Returns status string.
    """
    return await run_op(advanced_features.create_table, file_path=file_path, range_string=range_string, table_name=table_name, style_name=style_name)

@mcp.tool()
async def protect_sheet(file_path: str, password: str = None, enable_select_locked: bool = True) -> str:
    """PROTECTS sheet. [ACTION]
    
    [RAG Context]
    Enable sheet protection with optional password.
    Returns status string.
    """
    return await run_op(advanced_features.protect_sheet, file_path=file_path, password=password, enable_select_locked=enable_select_locked)

@mcp.tool()
async def add_defined_name(file_path: str, name: str, ref: str) -> str:
    """ADDS named range. [ACTION]
    
    [RAG Context]
    Create a new named range.
    Returns status string.
    """
    return await run_op(advanced_features.add_defined_name, file_path=file_path, name=name, ref=ref)

# 11. Structure & View
@mcp.tool()
async def group_rows(file_path: str, start_row: int, end_row: int, level: int = 1) -> str:
    """GROUPS rows. [ACTION]
    
    [RAG Context]
    Group/outline rows for collapsing.
    Returns status string.
    """
    return await run_op(structure_ops.group_rows, file_path=file_path, start_row=start_row, end_row=end_row, level=level)

@mcp.tool()
async def ungroup_rows(file_path: str, start_row: int, end_row: int) -> str:
    """UNGROUPS rows. [ACTION]
    
    [RAG Context]
    Remove row grouping/outline.
    Returns status string.
    """
    return await run_op(structure_ops.ungroup_rows, file_path=file_path, start_row=start_row, end_row=end_row)

@mcp.tool()
async def group_cols(file_path: str, start_col: str, end_col: str) -> str:
    """GROUPS cols. [ACTION]
    
    [RAG Context]
    Group/outline columns for collapsing.
    Returns status string.
    """
    return await run_op(structure_ops.group_cols, file_path=file_path, start_col=start_col, end_col=end_col)

@mcp.tool()
async def freeze_panes(file_path: str, cell: str) -> str:
    """FREEZES panes. [ACTION]
    
    [RAG Context]
    Freeze rows/cols above and left of cell.
    Returns status string.
    """
    return await run_op(structure_ops.freeze_panes, file_path=file_path, cell=cell)

@mcp.tool()
async def set_zoom_scale(file_path: str, zoom: int) -> str:
    """SETS zoom. [ACTION]
    
    [RAG Context]
    Set window zoom level (e.g., 100).
    Returns status string.
    """
    return await run_op(structure_ops.set_zoom_scale, file_path=file_path, zoom=zoom)

# 12. Analytics & Formula
# 12. Analytics & Formula
@mcp.tool()
async def create_pivot_table(file_path: str) -> str:
    """CREATES PivotTable. [ACTION]
    
    [RAG Context]
    Create a PivotTable (definition only).
    Returns status string.
    """
    return await run_op(analytics_ops.create_pivot_table, file_path=file_path)

@mcp.tool()
async def tokenize_formula(formula: str) -> str:
    """TOKENIZES formula. [ACTION]
    
    [RAG Context]
    Parse formula into tokens.
    Returns JSON string.
    """
    return await run_op(formula_ops.tokenize_formula, formula=formula)

@mcp.tool()
async def get_formula_references(formula: str) -> str:
    """FETCHES formula refs. [ACTION]
    
    [RAG Context]
    Extract cell references from formula.
    Returns list string.
    """
    return await run_op(formula_ops.get_formula_references, formula=formula)

# 13. Metadata
@mcp.tool()
async def check_vba_project(file_path: str) -> str:
    """CHECKS VBA. [ACTION]
    
    [RAG Context]
    Check if workbook contains VBA macros.
    Returns boolean string.
    """
    return await run_op(metadata_ops.check_vba_project, file_path=file_path)

@mcp.tool()
async def set_custom_property(file_path: str, name: str, value: str, type: str = "text") -> str:
    """SETS custom prop. [ACTION]
    
    [RAG Context]
    Add custom metadata property to workbook.
    Returns status string.
    """
    return await run_op(metadata_ops.set_custom_property, file_path=file_path, name=name, value=value, type=type)

# 14. Data Intelligence
@mcp.tool()
async def clean_whitespace(file_path: str, sheet_name: str = None, range_string: str = None) -> str:
    """CLEANS whitespace. [ACTION]
    
    [RAG Context]
    Trim leading/trailing whitespace from cells.
    Returns status string.
    """
    return await run_op(clean_ops.clean_whitespace, file_path=file_path, sheet_name=sheet_name, range_string=range_string)

@mcp.tool()
async def remove_duplicates(file_path: str, sheet_name: str = None, subset: list = None, header_row: int = 1) -> str:
    """REMOVES duplicates. [ACTION]
    
    [RAG Context]
    Remove duplicate rows based on columns.
    Returns status string.
    """
    return await run_op(clean_ops.remove_duplicates, file_path=file_path, sheet_name=sheet_name, subset=subset, header_row=header_row)

@mcp.tool()
async def convert_to_numbers(file_path: str, sheet_name: str = None) -> str:
    """CONVERTS to numbers. [ACTION]
    
    [RAG Context]
    Convert text-formatted numbers to numeric.
    Returns status string.
    """
    return await run_op(clean_ops.convert_to_numbers, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def find_error_cells(file_path: str, sheet_name: str = None) -> str:
    """FINDS error cells. [ACTION]
    
    [RAG Context]
    List cells with errors (e.g., #VALUE!).
    Returns list string.
    """
    return await run_op(audit_ops.find_error_cells, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def list_all_formulas(file_path: str, sheet_name: str = None) -> str:
    """LISTS formulas. [ACTION]
    
    [RAG Context]
    Get all formulas in the sheet.
    Returns table string.
    """
    return await run_op(audit_ops.list_all_formulas, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def render_template(file_path: str, replacements: dict, sheet_name: str = None) -> str:
    """RENDERS template. [ACTION]
    
    [RAG Context]
    Replace {{variables}} in cells with values.
    Returns status string.
    """
    return await run_op(template_ops.render_template, file_path=file_path, replacements=replacements, sheet_name=sheet_name)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class OpenpyxlServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
