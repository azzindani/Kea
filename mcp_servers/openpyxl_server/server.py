
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


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    workbook_ops, sheet_ops, read_ops, write_ops, manage_rows_cols,
    style_ops, chart_ops, object_ops, formatting_ops, advanced_features,
    structure_ops, analytics_ops, formula_ops, metadata_ops, clean_ops,
    audit_ops, template_ops
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
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
@mcp.tool()
async def analyze_workbook_file(file_path: str) -> str:
    """Analyze structure, sheets, ranges, and stats."""
    return await run_op(workbook_ops.analyze_workbook_file, file_path=file_path)

# 2. Workbook
@mcp.tool()
async def create_new_workbook(file_path: str, overwrite: bool = False) -> str:
    """Create new empty .xlsx."""
    return await run_op(workbook_ops.create_new_workbook, file_path=file_path, overwrite=overwrite)

@mcp.tool()
async def get_workbook_metadata(file_path: str) -> str:
    """Get author, dates."""
    return await run_op(workbook_ops.get_workbook_metadata, file_path=file_path)

@mcp.tool()
async def list_named_ranges(file_path: str) -> str:
    """List defined names."""
    return await run_op(workbook_ops.list_named_ranges, file_path=file_path)

# 3. Sheet Ops
@mcp.tool()
async def list_worksheets(file_path: str) -> str:
    """List all sheets."""
    return await run_op(sheet_ops.list_worksheets, file_path=file_path)

@mcp.tool()
async def create_worksheet(file_path: str, title: str, index: int = None) -> str:
    """Add sheet."""
    return await run_op(sheet_ops.create_worksheet, file_path=file_path, title=title, index=index)

@mcp.tool()
async def delete_worksheet(file_path: str, sheet_name: str) -> str:
    """Delete sheet."""
    return await run_op(sheet_ops.delete_worksheet, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def rename_worksheet(file_path: str, old_name: str, new_name: str) -> str:
    """Rename sheet."""
    return await run_op(sheet_ops.rename_worksheet, file_path=file_path, old_name=old_name, new_name=new_name)

@mcp.tool()
async def copy_worksheet(file_path: str, source_sheet: str, new_title: str) -> str:
    """Copy sheet."""
    return await run_op(sheet_ops.copy_worksheet, file_path=file_path, source_sheet=source_sheet, new_title=new_title)

@mcp.tool()
async def get_sheet_properties(file_path: str, sheet_name: str) -> str:
    """Get tab color etc."""
    return await run_op(sheet_ops.get_sheet_properties, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def set_sheet_properties(file_path: str, sheet_name: str, tab_color: str = None, state: str = None) -> str:
    """Set tab color etc."""
    return await run_op(sheet_ops.set_sheet_properties, file_path=file_path, sheet_name=sheet_name, tab_color=tab_color, state=state)

# 4. Reading
@mcp.tool()
async def read_excel_multitalent(file_path: str, sheet_name: str = None, range_string: str = None, header_row: int = 1) -> str:
    """BULK READ: Flexible reader for ranges/sheets."""
    return await run_op(read_ops.read_excel_multitalent, file_path=file_path, sheet_name=sheet_name, range_string=range_string, header_row=header_row)

@mcp.tool()
async def read_cell_value(file_path: str, cell: str, sheet_name: str = None) -> str:
    """Read single cell."""
    return await run_op(read_ops.read_cell_value, file_path=file_path, cell=cell, sheet_name=sheet_name)

@mcp.tool()
async def search_excel_content(file_path: str, query: str, is_regex: bool = False) -> str:
    """Search text/regex across workbook."""
    return await run_op(read_ops.search_excel_content, file_path=file_path, query=query, is_regex=is_regex)

@mcp.tool()
async def read_range_values(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """Read range (Values)."""
    return await run_op(read_ops.read_range_values, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 5. Writing
@mcp.tool()
async def write_cell_value(file_path: str, cell: str, value: str, sheet_name: str = None) -> str:
    """Write cell."""
    return await run_op(write_ops.write_cell_value, file_path=file_path, cell=cell, value=value, sheet_name=sheet_name)

@mcp.tool()
async def write_range_values(file_path: str, data: list, start_cell: str = "A1", sheet_name: str = None) -> str:
    """Write bulk data range."""
    return await run_op(write_ops.write_range_values, file_path=file_path, data=data, start_cell=start_cell, sheet_name=sheet_name)

@mcp.tool()
async def write_formula(file_path: str, cell: str, formula: str, sheet_name: str = None) -> str:
    """Write formula string."""
    return await run_op(write_ops.write_formula, file_path=file_path, cell=cell, formula=formula, sheet_name=sheet_name)

@mcp.tool()
async def clear_range(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """Clear values in range."""
    return await run_op(write_ops.clear_range, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 6. Struct Editing
@mcp.tool()
async def insert_rows(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """Insert rows."""
    return await run_op(manage_rows_cols.insert_rows, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def delete_rows(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """Delete rows."""
    return await run_op(manage_rows_cols.delete_rows, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def insert_cols(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """Insert cols."""
    return await run_op(manage_rows_cols.insert_cols, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def delete_cols(file_path: str, idx: int, amount: int = 1, sheet_name: str = None) -> str:
    """Delete cols."""
    return await run_op(manage_rows_cols.delete_cols, file_path=file_path, idx=idx, amount=amount, sheet_name=sheet_name)

@mcp.tool()
async def move_range(file_path: str, range_string: str, rows: int, cols: int, sheet_name: str = None) -> str:
    """Move/Translate range."""
    return await run_op(manage_rows_cols.move_range, file_path=file_path, range_string=range_string, rows=rows, cols=cols, sheet_name=sheet_name)

# 7. Styling
@mcp.tool()
async def set_cell_font(file_path: str, cell: str, font_name: str = None, size: float = None, bold: bool = None, color: str = None) -> str:
    """Set font props."""
    return await run_op(style_ops.set_cell_font, file_path=file_path, cell=cell, font_name=font_name, size=size, bold=bold, color=color)

@mcp.tool()
async def set_cell_fill(file_path: str, cell: str, color: str, sheet_name: str = None) -> str:
    """Set background color."""
    return await run_op(style_ops.set_cell_fill, file_path=file_path, cell=cell, color=color, sheet_name=sheet_name)

@mcp.tool()
async def set_cell_border(file_path: str, cell: str, style: str = "thin", color: str = "000000") -> str:
    """Set borders."""
    return await run_op(style_ops.set_cell_border, file_path=file_path, cell=cell, style=style, color=color)

@mcp.tool()
async def merge_cells(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """Merge range."""
    return await run_op(style_ops.merge_cells, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

@mcp.tool()
async def unmerge_cells(file_path: str, range_string: str, sheet_name: str = None) -> str:
    """Unmerge range."""
    return await run_op(style_ops.unmerge_cells, file_path=file_path, range_string=range_string, sheet_name=sheet_name)

# 8. Advanced (Charts/Objects)
@mcp.tool()
async def create_chart(file_path: str, type: str, data_range: str, title: str = None, anchor: str = "E5") -> str:
    """Add Chart."""
    return await run_op(chart_ops.create_chart, file_path=file_path, type=type, data_range=data_range, title=title, anchor=anchor)

@mcp.tool()
async def add_image_to_sheet(file_path: str, image_path: str, anchor: str = "A1") -> str:
    """Insert Image."""
    return await run_op(object_ops.add_image_to_sheet, file_path=file_path, image_path=image_path, anchor=anchor)

@mcp.tool()
async def add_comment(file_path: str, cell: str, text: str, author: str = "AI") -> str:
    """Add Comment."""
    return await run_op(object_ops.add_comment, file_path=file_path, cell=cell, text=text, author=author)

@mcp.tool()
async def read_comments(file_path: str, sheet_name: str = None) -> str:
    """Read all comments."""
    return await run_op(object_ops.read_comments, file_path=file_path, sheet_name=sheet_name)

# 9. Formatting
@mcp.tool()
async def add_color_scale(file_path: str, range_string: str, start_color: str = "F8696B", mid_color: str = "FFEB84", end_color: str = "63BE7B") -> str:
    """Add Color Scale CF."""
    return await run_op(formatting_ops.add_color_scale, file_path=file_path, range_string=range_string, start_color=start_color, mid_color=mid_color, end_color=end_color)

@mcp.tool()
async def add_data_bar(file_path: str, range_string: str, color: str = "638EC6") -> str:
    """Add Data Bar CF."""
    return await run_op(formatting_ops.add_data_bar, file_path=file_path, range_string=range_string, color=color)

@mcp.tool()
async def add_highlight_rule(file_path: str, range_string: str, operator: str, formula: list = None, fill_color: str = "FFC7CE", font_color: str = "9C0006", bold: bool = False) -> str:
    """Add Highlight Rule."""
    return await run_op(formatting_ops.add_highlight_rule, file_path=file_path, range_string=range_string, operator=operator, formula=formula, fill_color=fill_color, font_color=font_color, bold=bold)

@mcp.tool()
async def set_page_setup(file_path: str, orientation: str = None, paper_size: int = None, fit_to_width: int = None, fit_to_height: int = None) -> str:
    """Set Page Setup."""
    return await run_op(formatting_ops.set_page_setup, file_path=file_path, orientation=orientation, paper_size=paper_size, fit_to_width=fit_to_width, fit_to_height=fit_to_height)

@mcp.tool()
async def set_print_area(file_path: str, print_area: str) -> str:
    """Set Print Area."""
    return await run_op(formatting_ops.set_print_area, file_path=file_path, print_area=print_area)

# 10. Advanced Features
@mcp.tool()
async def add_list_validation(file_path: str, cell_range: str, options: list = None, formula: str = None) -> str:
    """Add Dropdown List."""
    return await run_op(advanced_features.add_list_validation, file_path=file_path, cell_range=cell_range, options=options, formula=formula)

@mcp.tool()
async def create_table(file_path: str, range_string: str, table_name: str = None, style_name: str = "TableStyleMedium9") -> str:
    """Create Excel Table."""
    return await run_op(advanced_features.create_table, file_path=file_path, range_string=range_string, table_name=table_name, style_name=style_name)

@mcp.tool()
async def protect_sheet(file_path: str, password: str = None, enable_select_locked: bool = True) -> str:
    """Protect Sheet."""
    return await run_op(advanced_features.protect_sheet, file_path=file_path, password=password, enable_select_locked=enable_select_locked)

@mcp.tool()
async def add_defined_name(file_path: str, name: str, ref: str) -> str:
    """Add Named Range."""
    return await run_op(advanced_features.add_defined_name, file_path=file_path, name=name, ref=ref)

# 11. Structure & View
@mcp.tool()
async def group_rows(file_path: str, start_row: int, end_row: int, level: int = 1) -> str:
    """Group Rows."""
    return await run_op(structure_ops.group_rows, file_path=file_path, start_row=start_row, end_row=end_row, level=level)

@mcp.tool()
async def ungroup_rows(file_path: str, start_row: int, end_row: int) -> str:
    """Ungroup Rows."""
    return await run_op(structure_ops.ungroup_rows, file_path=file_path, start_row=start_row, end_row=end_row)

@mcp.tool()
async def group_cols(file_path: str, start_col: str, end_col: str) -> str:
    """Group Columns."""
    return await run_op(structure_ops.group_cols, file_path=file_path, start_col=start_col, end_col=end_col)

@mcp.tool()
async def freeze_panes(file_path: str, cell: str) -> str:
    """Freeze Panes."""
    return await run_op(structure_ops.freeze_panes, file_path=file_path, cell=cell)

@mcp.tool()
async def set_zoom_scale(file_path: str, zoom: int) -> str:
    """Set Zoom."""
    return await run_op(structure_ops.set_zoom_scale, file_path=file_path, zoom=zoom)

# 12. Analytics & Formula
@mcp.tool()
async def create_pivot_table(file_path: str) -> str:
    """Create PivotTable Def."""
    return await run_op(analytics_ops.create_pivot_table, file_path=file_path)

@mcp.tool()
async def tokenize_formula(formula: str) -> str:
    """Tokenize Formula."""
    return await run_op(formula_ops.tokenize_formula, formula=formula)

@mcp.tool()
async def get_formula_references(formula: str) -> str:
    """Get Formula Refs."""
    return await run_op(formula_ops.get_formula_references, formula=formula)

# 13. Metadata
@mcp.tool()
async def check_vba_project(file_path: str) -> str:
    """Check VBA."""
    return await run_op(metadata_ops.check_vba_project, file_path=file_path)

@mcp.tool()
async def set_custom_property(file_path: str, name: str, value: str, type: str = "text") -> str:
    """Set Custom Prop."""
    return await run_op(metadata_ops.set_custom_property, file_path=file_path, name=name, value=value, type=type)

# 14. Data Intelligence
@mcp.tool()
async def clean_whitespace(file_path: str, sheet_name: str = None, range_string: str = None) -> str:
    """Trim strings."""
    return await run_op(clean_ops.clean_whitespace, file_path=file_path, sheet_name=sheet_name, range_string=range_string)

@mcp.tool()
async def remove_duplicates(file_path: str, sheet_name: str = None, subset: list = None, header_row: int = 1) -> str:
    """Remove Duplicate Rows."""
    return await run_op(clean_ops.remove_duplicates, file_path=file_path, sheet_name=sheet_name, subset=subset, header_row=header_row)

@mcp.tool()
async def convert_to_numbers(file_path: str, sheet_name: str = None) -> str:
    """Convert Text to Numbers."""
    return await run_op(clean_ops.convert_to_numbers, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def find_error_cells(file_path: str, sheet_name: str = None) -> str:
    """List Error Cells."""
    return await run_op(audit_ops.find_error_cells, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def list_all_formulas(file_path: str, sheet_name: str = None) -> str:
    """List All Formulas."""
    return await run_op(audit_ops.list_all_formulas, file_path=file_path, sheet_name=sheet_name)

@mcp.tool()
async def render_template(file_path: str, replacements: dict, sheet_name: str = None) -> str:
    """Render {{vars}}."""
    return await run_op(template_ops.render_template, file_path=file_path, replacements=replacements, sheet_name=sheet_name)

if __name__ == "__main__":
    mcp.run()