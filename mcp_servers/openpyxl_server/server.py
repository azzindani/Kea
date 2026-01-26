
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger
import asyncio

# Import Tool Handlers
from mcp_servers.openpyxl_server.tools.workbook_ops import (
    analyze_workbook_file, create_new_workbook, get_workbook_metadata, list_named_ranges
)
from mcp_servers.openpyxl_server.tools.sheet_ops import (
    list_worksheets, create_worksheet, delete_worksheet, rename_worksheet,
    copy_worksheet, get_sheet_properties, set_sheet_properties
)
from mcp_servers.openpyxl_server.tools.read_ops import (
    read_excel_multitalent, read_cell_value, search_excel_content, read_range_values
)
from mcp_servers.openpyxl_server.tools.write_ops import (
    write_cell_value, write_range_values, write_formula, clear_range
)
from mcp_servers.openpyxl_server.tools.manage_rows_cols import (
    insert_rows, delete_rows, insert_cols, delete_cols, move_range
)
from mcp_servers.openpyxl_server.tools.style_ops import (
    set_cell_font, set_cell_fill, set_cell_border, merge_cells, unmerge_cells
)
from mcp_servers.openpyxl_server.tools.chart_ops import create_chart
from mcp_servers.openpyxl_server.tools.object_ops import (
    add_image_to_sheet, add_comment, read_comments
)
from mcp_servers.openpyxl_server.tools.formatting_ops import (
    add_color_scale, add_data_bar, add_highlight_rule, set_page_setup, set_print_area
)
from mcp_servers.openpyxl_server.tools.advanced_features import (
    add_list_validation, create_table, protect_sheet, add_defined_name
)
from mcp_servers.openpyxl_server.tools.structure_ops import (
    group_rows, ungroup_rows, group_cols, freeze_panes, set_zoom_scale
)
from mcp_servers.openpyxl_server.tools.analytics_ops import create_pivot_table
from mcp_servers.openpyxl_server.tools.formula_ops import tokenize_formula, get_formula_references
from mcp_servers.openpyxl_server.tools.metadata_ops import check_vba_project, set_custom_property
from mcp_servers.openpyxl_server.tools.clean_ops import clean_whitespace, remove_duplicates, convert_to_numbers
from mcp_servers.openpyxl_server.tools.audit_ops import find_error_cells, list_all_formulas
from mcp_servers.openpyxl_server.tools.template_ops import render_template

logger = get_logger(__name__)

class OpenPyXLServer(MCPServer):
    """
    OpenPyXL Server for advanced Excel manipulation.
    """
    def __init__(self):
        super().__init__("openpyxl_server", "1.0.0")
        self._register_tools()
        
    def _register_tools(self):
        # 1. Multitalent / Super Tools
        self.register_tool(name="analyze_workbook_file", description="Analyze structure, sheets, ranges, and stats.", handler=analyze_workbook_file, parameters={"file_path": {"type": "string"}})
        
        # 2. Workbook
        self.register_tool(name="create_new_workbook", description="Create empty .xlsx.", handler=create_new_workbook, parameters={"file_path": {"type": "string"}, "overwrite": {"type": "boolean"}})
        self.register_tool(name="get_workbook_metadata", description="Get author, dates.", handler=get_workbook_metadata, parameters={"file_path": {"type": "string"}})
        self.register_tool(name="list_named_ranges", description="List defined names.", handler=list_named_ranges, parameters={"file_path": {"type": "string"}})
        
        # 3. Sheet Ops
        self.register_tool(name="list_worksheets", description="List all sheets.", handler=list_worksheets, parameters={"file_path": {"type": "string"}})
        self.register_tool(name="create_worksheet", description="Add sheet.", handler=create_worksheet, parameters={"file_path": {"type": "string"}, "title": {"type": "string"}, "index": {"type": "integer"}})
        self.register_tool(name="delete_worksheet", description="Delete sheet.", handler=delete_worksheet, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="rename_worksheet", description="Rename sheet.", handler=rename_worksheet, parameters={"file_path": {"type": "string"}, "old_name": {"type": "string"}, "new_name": {"type": "string"}})
        self.register_tool(name="copy_worksheet", description="Copy sheet.", handler=copy_worksheet, parameters={"file_path": {"type": "string"}, "source_sheet": {"type": "string"}, "new_title": {"type": "string"}})
        self.register_tool(name="get_sheet_properties", description="Get tab color etc.", handler=get_sheet_properties, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="set_sheet_properties", description="Set tab color etc.", handler=set_sheet_properties, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "tab_color": {"type": "string"}, "state": {"type": "string"}})
        
        # 4. Reading
        self.register_tool(name="read_excel_multitalent", description="BULK READ: Flexible reader for ranges/sheets.", handler=read_excel_multitalent, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "range_string": {"type": "string"}, "header_row": {"type": "integer"}})
        self.register_tool(name="read_cell_value", description="Read single cell.", handler=read_cell_value, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="search_excel_content", description="Search text/regex across workbook.", handler=search_excel_content, parameters={"file_path": {"type": "string"}, "query": {"type": "string"}, "is_regex": {"type": "boolean"}})
        self.register_tool(name="read_range_values", description="Read range (Values).", handler=read_range_values, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "sheet_name": {"type": "string"}})
        
        # 5. Writing
        self.register_tool(name="write_cell_value", description="Write cell.", handler=write_cell_value, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "value": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="write_range_values", description="Write bulk data range.", handler=write_range_values, parameters={"file_path": {"type": "string"}, "data": {"type": "array"}, "start_cell": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="write_formula", description="Write formula string.", handler=write_formula, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "formula": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="clear_range", description="Clear values in range.", handler=clear_range, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "sheet_name": {"type": "string"}})
        
        # 6. Struct Editing
        self.register_tool(name="insert_rows", description="Insert rows.", handler=insert_rows, parameters={"file_path": {"type": "string"}, "idx": {"type": "integer"}, "amount": {"type": "integer"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="delete_rows", description="Delete rows.", handler=delete_rows, parameters={"file_path": {"type": "string"}, "idx": {"type": "integer"}, "amount": {"type": "integer"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="insert_cols", description="Insert cols.", handler=insert_cols, parameters={"file_path": {"type": "string"}, "idx": {"type": "integer"}, "amount": {"type": "integer"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="delete_cols", description="Delete cols.", handler=delete_cols, parameters={"file_path": {"type": "string"}, "idx": {"type": "integer"}, "amount": {"type": "integer"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="move_range", description="Move/Translate range.", handler=move_range, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "rows": {"type": "integer"}, "cols": {"type": "integer"}, "sheet_name": {"type": "string"}})
        
        # 7. Styling
        self.register_tool(name="set_cell_font", description="Set font props.", handler=set_cell_font, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "font_name": {"type": "string"}, "size": {"type": "number"}, "bold": {"type": "boolean"}, "color": {"type": "string"}})
        self.register_tool(name="set_cell_fill", description="Set background color.", handler=set_cell_fill, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "color": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="set_cell_border", description="Set borders.", handler=set_cell_border, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "style": {"type": "string"}, "color": {"type": "string"}})
        self.register_tool(name="merge_cells", description="Merge range.", handler=merge_cells, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="unmerge_cells", description="Unmerge range.", handler=unmerge_cells, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "sheet_name": {"type": "string"}})
        
        
        # 8. Advanced (Charts/Objects)
        self.register_tool(name="create_chart", description="Add Chart.", handler=create_chart, parameters={"file_path": {"type": "string"}, "type": {"type": "string"}, "data_range": {"type": "string"}, "title": {"type": "string"}, "anchor": {"type": "string"}})
        
        self.register_tool(name="add_image_to_sheet", description="Insert Image.", handler=add_image_to_sheet, parameters={"file_path": {"type": "string"}, "image_path": {"type": "string"}, "anchor": {"type": "string"}})
        self.register_tool(name="add_comment", description="Add Comment.", handler=add_comment, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}, "text": {"type": "string"}, "author": {"type": "string"}})
        self.register_tool(name="read_comments", description="Read all comments.", handler=read_comments, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        
        # 9. Formatting (Phase 2)
        self.register_tool(name="add_color_scale", description="Add Color Scale CF.", handler=add_color_scale, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "start_color": {"type": "string"}, "mid_color": {"type": "string"}, "end_color": {"type": "string"}})
        self.register_tool(name="add_data_bar", description="Add Data Bar CF.", handler=add_data_bar, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "color": {"type": "string"}})
        self.register_tool(name="add_highlight_rule", description="Add Highlight Rule.", handler=add_highlight_rule, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "operator": {"type": "string"}, "formula": {"type": "array"}, "fill_color": {"type": "string"}, "font_color": {"type": "string"}, "bold": {"type": "boolean"}})
        self.register_tool(name="set_page_setup", description="Set Page Setup.", handler=set_page_setup, parameters={"file_path": {"type": "string"}, "orientation": {"type": "string"}, "paper_size": {"type": "integer"}, "fit_to_width": {"type": "integer"}, "fit_to_height": {"type": "integer"}})
        self.register_tool(name="set_print_area", description="Set Print Area.", handler=set_print_area, parameters={"file_path": {"type": "string"}, "print_area": {"type": "string"}})
        
        # 10. Advanced Features (Phase 2)
        self.register_tool(name="add_list_validation", description="Add Dropdown List.", handler=add_list_validation, parameters={"file_path": {"type": "string"}, "cell_range": {"type": "string"}, "options": {"type": "array"}, "formula": {"type": "string"}})
        self.register_tool(name="create_table", description="Create Excel Table.", handler=create_table, parameters={"file_path": {"type": "string"}, "range_string": {"type": "string"}, "table_name": {"type": "string"}, "style_name": {"type": "string"}})
        self.register_tool(name="protect_sheet", description="Protect Sheet.", handler=protect_sheet, parameters={"file_path": {"type": "string"}, "password": {"type": "string"}, "enable_select_locked": {"type": "boolean"}})
        self.register_tool(name="add_defined_name", description="Add Named Range.", handler=add_defined_name, parameters={"file_path": {"type": "string"}, "name": {"type": "string"}, "ref": {"type": "string"}})
        
        # 11. Structure & View (Phase 3)
        self.register_tool(name="group_rows", description="Group Rows.", handler=group_rows, parameters={"file_path": {"type": "string"}, "start_row": {"type": "integer"}, "end_row": {"type": "integer"}, "level": {"type": "integer"}})
        self.register_tool(name="ungroup_rows", description="Ungroup Rows.", handler=ungroup_rows, parameters={"file_path": {"type": "string"}, "start_row": {"type": "integer"}, "end_row": {"type": "integer"}})
        self.register_tool(name="group_cols", description="Group Columns.", handler=group_cols, parameters={"file_path": {"type": "string"}, "start_col": {"type": "string"}, "end_col": {"type": "string"}})
        self.register_tool(name="freeze_panes", description="Freeze Panes.", handler=freeze_panes, parameters={"file_path": {"type": "string"}, "cell": {"type": "string"}})
        self.register_tool(name="set_zoom_scale", description="Set Zoom.", handler=set_zoom_scale, parameters={"file_path": {"type": "string"}, "zoom": {"type": "integer"}})
        
        # 12. Analytics & Formula (Phase 3)
        self.register_tool(name="create_pivot_table", description="Create PivotTable Def.", handler=create_pivot_table, parameters={"file_path": {"type": "string"}})
        self.register_tool(name="tokenize_formula", description="Tokenize Formula.", handler=tokenize_formula, parameters={"formula": {"type": "string"}})
        self.register_tool(name="get_formula_references", description="Get Formula Refs.", handler=get_formula_references, parameters={"formula": {"type": "string"}})
        
        # 13. Metadata (Phase 3)
        self.register_tool(name="check_vba_project", description="Check VBA.", handler=check_vba_project, parameters={"file_path": {"type": "string"}})
        self.register_tool(name="set_custom_property", description="Set Custom Prop.", handler=set_custom_property, parameters={"file_path": {"type": "string"}, "name": {"type": "string"}, "value": {"type": "string"}, "type": {"type": "string"}})
        
        # 14. Data Intelligence (Phase 4)
        self.register_tool(name="clean_whitespace", description="Trim strings.", handler=clean_whitespace, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "range_string": {"type": "string"}})
        self.register_tool(name="remove_duplicates", description="Remove Duplicate Rows.", handler=remove_duplicates, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "subset": {"type": "array"}, "header_row": {"type": "integer"}})
        self.register_tool(name="convert_to_numbers", description="Convert Text to Numbers.", handler=convert_to_numbers, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="find_error_cells", description="List Error Cells.", handler=find_error_cells, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="list_all_formulas", description="List All Formulas.", handler=list_all_formulas, parameters={"file_path": {"type": "string"}, "sheet_name": {"type": "string"}})
        self.register_tool(name="render_template", description="Render {{vars}}.", handler=render_template, parameters={"file_path": {"type": "string"}, "replacements": {"type": "object"}, "sheet_name": {"type": "string"}})

if __name__ == "__main__":
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="openpyxl_server"))
    asyncio.run(OpenPyXLServer().run())
