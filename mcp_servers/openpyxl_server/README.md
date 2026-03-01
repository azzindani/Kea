# 🔌 Openpyxl Server

The `openpyxl_server` is an MCP server providing tools for **Openpyxl Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `analyze_workbook_file` | Execute analyze workbook file operation | `file_path: str` |
| `create_new_workbook` | Execute create new workbook operation | `file_path: str, overwrite: bool = False` |
| `get_workbook_metadata` | Execute get workbook metadata operation | `file_path: str` |
| `list_named_ranges` | Execute list named ranges operation | `file_path: str` |
| `list_worksheets` | Execute list worksheets operation | `file_path: str` |
| `create_worksheet` | Execute create worksheet operation | `file_path: str, title: str, index: int = None` |
| `delete_worksheet` | Execute delete worksheet operation | `file_path: str, sheet_name: str` |
| `rename_worksheet` | Execute rename worksheet operation | `file_path: str, old_name: str, new_name: str` |
| `copy_worksheet` | Execute copy worksheet operation | `file_path: str, source_sheet: str, new_title: str` |
| `get_sheet_properties` | Execute get sheet properties operation | `file_path: str, sheet_name: str` |
| `set_sheet_properties` | Execute set sheet properties operation | `file_path: str, sheet_name: str, tab_color: str = None, state: str = None` |
| `read_excel_multitalent` | Execute read excel multitalent operation | `file_path: str, sheet_name: str = None, range_string: str = None, header_row: int = 1` |
| `read_cell_value` | Execute read cell value operation | `file_path: str, cell: str, sheet_name: str = None` |
| `search_excel_content` | Execute search excel content operation | `file_path: str, query: str, is_regex: bool = False` |
| `read_range_values` | Execute read range values operation | `file_path: str, range_string: str, sheet_name: str = None` |
| `write_cell_value` | Execute write cell value operation | `file_path: str, cell: str, value: str, sheet_name: str = None` |
| `write_range_values` | Execute write range values operation | `file_path: str, data: list, start_cell: str = "A1", sheet_name: str = None` |
| `write_formula` | Execute write formula operation | `file_path: str, cell: str, formula: str, sheet_name: str = None` |
| `clear_range` | Execute clear range operation | `file_path: str, range_string: str, sheet_name: str = None` |
| `insert_rows` | Execute insert rows operation | `file_path: str, idx: int, amount: int = 1, sheet_name: str = None` |
| `delete_rows` | Execute delete rows operation | `file_path: str, idx: int, amount: int = 1, sheet_name: str = None` |
| `insert_cols` | Execute insert cols operation | `file_path: str, idx: int, amount: int = 1, sheet_name: str = None` |
| `delete_cols` | Execute delete cols operation | `file_path: str, idx: int, amount: int = 1, sheet_name: str = None` |
| `move_range` | Execute move range operation | `file_path: str, range_string: str, rows: int, cols: int, sheet_name: str = None` |
| `set_cell_font` | Execute set cell font operation | `file_path: str, cell: str, font_name: str = None, size: float = None, bold: bool = None, color: str = None` |
| `set_cell_fill` | Execute set cell fill operation | `file_path: str, cell: str, color: str, sheet_name: str = None` |
| `set_cell_border` | Execute set cell border operation | `file_path: str, cell: str, style: str = "thin", color: str = "000000"` |
| `merge_cells` | Execute merge cells operation | `file_path: str, range_string: str, sheet_name: str = None` |
| `unmerge_cells` | Execute unmerge cells operation | `file_path: str, range_string: str, sheet_name: str = None` |
| `create_chart` | Execute create chart operation | `file_path: str, type: str, data_range: str, title: str = None, anchor: str = "E5"` |
| `add_image_to_sheet` | Execute add image to sheet operation | `file_path: str, image_path: str, anchor: str = "A1"` |
| `add_comment` | Execute add comment operation | `file_path: str, cell: str, text: str, author: str = "AI"` |
| `read_comments` | Execute read comments operation | `file_path: str, sheet_name: str = None` |
| `add_color_scale` | Execute add color scale operation | `file_path: str, range_string: str, start_color: str = "F8696B", mid_color: str = "FFEB84", end_color: str = "63BE7B"` |
| `add_data_bar` | Execute add data bar operation | `file_path: str, range_string: str, color: str = "638EC6"` |
| `add_highlight_rule` | Execute add highlight rule operation | `file_path: str, range_string: str, operator: str, formula: list = None, fill_color: str = "FFC7CE", font_color: str = "9C0006", bold: bool = False` |
| `set_page_setup` | Execute set page setup operation | `file_path: str, orientation: str = None, paper_size: int = None, fit_to_width: int = None, fit_to_height: int = None` |
| `set_print_area` | Execute set print area operation | `file_path: str, print_area: str` |
| `add_list_validation` | Execute add list validation operation | `file_path: str, cell_range: str, options: list = None, formula: str = None` |
| `create_table` | Execute create table operation | `file_path: str, range_string: str, table_name: str = None, style_name: str = "TableStyleMedium9"` |
| `protect_sheet` | Execute protect sheet operation | `file_path: str, password: str = None, enable_select_locked: bool = True` |
| `add_defined_name` | Execute add defined name operation | `file_path: str, name: str, ref: str` |
| `group_rows` | Execute group rows operation | `file_path: str, start_row: int, end_row: int, level: int = 1` |
| `ungroup_rows` | Execute ungroup rows operation | `file_path: str, start_row: int, end_row: int` |
| `group_cols` | Execute group cols operation | `file_path: str, start_col: str, end_col: str` |
| `freeze_panes` | Execute freeze panes operation | `file_path: str, cell: str` |
| `set_zoom_scale` | Execute set zoom scale operation | `file_path: str, zoom: int` |
| `create_pivot_table` | Execute create pivot table operation | `file_path: str` |
| `tokenize_formula` | Execute tokenize formula operation | `formula: str` |
| `get_formula_references` | Execute get formula references operation | `formula: str` |
| `check_vba_project` | Execute check vba project operation | `file_path: str` |
| `set_custom_property` | Execute set custom property operation | `file_path: str, name: str, value: str, type: str = "text"` |
| `clean_whitespace` | Execute clean whitespace operation | `file_path: str, sheet_name: str = None, range_string: str = None` |
| `remove_duplicates` | Execute remove duplicates operation | `file_path: str, sheet_name: str = None, subset: list = None, header_row: int = 1` |
| `convert_to_numbers` | Execute convert to numbers operation | `file_path: str, sheet_name: str = None` |
| `find_error_cells` | Execute find error cells operation | `file_path: str, sheet_name: str = None` |
| `list_all_formulas` | Execute list all formulas operation | `file_path: str, sheet_name: str = None` |
| `render_template` | Execute render template operation | `file_path: str, replacements: dict, sheet_name: str = None` |

## 📦 Dependencies

The following packages are required:
- `openpyxl`
- `pandas`
- `pillow`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.openpyxl_server.server
```
