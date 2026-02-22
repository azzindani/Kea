
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.docx_server.tools import (
    core_ops, text_ops, structure_ops, table_ops, 
    media_ops, style_ops, bulk_ops, super_ops
)
import structlog
from typing import List, Dict, Optional, Any

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("docx_server", dependencies=["python-docx", "pandas", "pillow"])

# ==========================================
# 1. Core & Properties
# ==========================================
@mcp.tool()
def create_document_file(path: str) -> str: 
    """CREATES new empty Word doc. [ACTION]
    
    [RAG Context]
    """
    return core_ops.create_document_file(path)

@mcp.tool()
def validate_docx(path: str) -> dict: 
    """VALIDATES docx structure. [DATA]
    
    [RAG Context]
    """
    return core_ops.validate_docx(path)

@mcp.tool()
def get_document_properties(path: str) -> dict: 
    """READS doc properties. [DATA]
    
    [RAG Context]
    Author, Title, etc.
    """
    return core_ops.get_document_properties(path)

@mcp.tool()
def set_document_properties(path: str, author: str = None, title: str = None) -> str: 
    """WRITES doc properties. [ACTION]
    
    [RAG Context]
    """
    return core_ops.set_document_properties(path, author, title)

# ==========================================
# 2. Text & Paragraphs
# ==========================================
@mcp.tool()
def add_paragraph(path: str, text: str, style: Optional[str] = None) -> str: 
    """ADDS paragraph to doc. [ACTION]
    
    [RAG Context]
    """
    return text_ops.add_paragraph(path, text, style)

@mcp.tool()
def add_heading(path: str, text: str, level: int = 1) -> str: 
    """ADDS heading to doc. [ACTION]
    
    [RAG Context]
    """
    return text_ops.add_heading(path, text, level)

@mcp.tool()
def add_run(path: str, paragraph_index: int, text: str, bold: bool = False, italic: bool = False, color_rgb: Optional[List[int]] = None) -> str: 
    """ADDS styled text run. [ACTION]
    
    [RAG Context]
    """
    return text_ops.add_run(path, paragraph_index, text, bold, italic, color_rgb)

@mcp.tool()
def read_paragraphs(path: str) -> List[str]: 
    """READS all paragraphs. [DATA]
    
    [RAG Context]
    """
    return text_ops.read_paragraphs(path)

@mcp.tool()
def read_paragraph_at_index(path: str, index: int) -> str: 
    """READS specific paragraph. [DATA]
    
    [RAG Context]
    """
    return text_ops.read_paragraph_at_index(path, index)

@mcp.tool()
def insert_paragraph_before(path: str, index: int, text: str, style: Optional[str] = None) -> str: 
    """INSERTS paragraph at index. [ACTION]
    
    [RAG Context]
    """
    return text_ops.insert_paragraph_before(path, index, text, style)

@mcp.tool()
def delete_paragraph(path: str, index: int) -> str: 
    """DELETES paragraph. [ACTION]
    
    [RAG Context]
    """
    return text_ops.delete_paragraph(path, index)

@mcp.tool()
def replace_text(path: str, old_text: str, new_text: str) -> int: 
    """REPLACES text occurrences. [ACTION]
    
    [RAG Context]
    """
    return text_ops.replace_text(path, old_text, new_text)

@mcp.tool()
def get_text_stats(path: str) -> Dict[str, int]: 
    """COUNTS words/chars. [DATA]
    
    [RAG Context]
    """
    return text_ops.get_text_stats(path)

@mcp.tool()
def clear_document_content(path: str) -> str: 
    """REMOVES all content. [ACTION]
    
    [RAG Context]
    Make empty doc.
    """
    return text_ops.clear_document_content(path)

# ==========================================
# 3. Structure
# ==========================================
@mcp.tool()
def add_section(path: str, section_type: str = "NEXT_PAGE") -> str: 
    """ADDS new section. [ACTION]
    
    [RAG Context]
    """
    return structure_ops.add_section(path, section_type)

@mcp.tool()
def get_sections(path: str) -> List[Dict[str, Any]]: 
    """LISTS sections. [DATA]
    
    [RAG Context]
    """
    return structure_ops.get_sections(path)

@mcp.tool()
def set_header(path: str, section_index: int, text: str) -> str: 
    """SETS header text. [ACTION]
    
    [RAG Context]
    """
    return structure_ops.set_header(path, section_index, text)

@mcp.tool()
def set_footer(path: str, section_index: int, text: str) -> str: 
    """SETS footer text. [ACTION]
    
    [RAG Context]
    """
    return structure_ops.set_footer(path, section_index, text)

@mcp.tool()
def read_header(path: str, section_index: int) -> str: 
    """READS header text. [DATA]
    
    [RAG Context]
    """
    return structure_ops.read_header(path, section_index)

@mcp.tool()
def read_footer(path: str, section_index: int) -> str: 
    """READS footer text. [DATA]
    
    [RAG Context]
    """
    return structure_ops.read_footer(path, section_index)

@mcp.tool()
def add_page_break(path: str) -> str: 
    """ADDS page break. [ACTION]
    
    [RAG Context]
    """
    return structure_ops.add_page_break(path)

# ==========================================
# 4. Tables
# ==========================================
@mcp.tool()
def add_table(path: str, rows: int, cols: int, style: str = "Table Grid") -> str: 
    """ADDS empty table. [ACTION]
    
    [RAG Context]
    """
    return table_ops.add_table(path, rows, cols, style)

@mcp.tool()
def add_row(path: str, table_index: int, cells_text: List[str]) -> str: 
    """ADDS row to table. [ACTION]
    
    [RAG Context]
    """
    return table_ops.add_row(path, table_index, cells_text)

@mcp.tool()
def add_column(path: str, table_index: int, width_inches: float = 1.0) -> str: 
    """ADDS column to table. [ACTION]
    
    [RAG Context]
    """
    return table_ops.add_column(path, table_index, width_inches)

@mcp.tool()
def set_cell_text(path: str, table_index: int, row: int, col: int, text: str) -> str: 
    """SETS cell text. [ACTION]
    
    [RAG Context]
    """
    return table_ops.set_cell_text(path, table_index, row, col, text)

@mcp.tool()
def read_table(path: str, table_index: int) -> List[List[str]]: 
    """READS table content. [DATA]
    
    [RAG Context]
    """
    return table_ops.read_table(path, table_index)

@mcp.tool()
def read_all_tables(path: str) -> List[List[List[str]]]: 
    """READS all tables. [DATA]
    
    [RAG Context]
    """
    return table_ops.read_all_tables(path)

@mcp.tool()
def read_table_df(path: str, table_index: int) -> List[Dict[str, Any]]: 
    """READS table as list of dicts. [DATA]
    
    [RAG Context]
    """
    return table_ops.read_table_df(path, table_index)

@mcp.tool()
def style_table(path: str, table_index: int, style_name: str) -> str: 
    """SETS table style. [ACTION]
    
    [RAG Context]
    """
    return table_ops.style_table(path, table_index, style_name)

@mcp.tool()
def merge_cells(path: str, table_index: int, start_row: int, start_col: int, end_row: int, end_col: int) -> str: 
    """MERGES table cells. [ACTION]
    
    [RAG Context]
    """
    return table_ops.merge_cells(path, table_index, start_row, start_col, end_row, end_col)

# ==========================================
# 5. Media & Styles
# ==========================================
# ==========================================
# 5. Media & Styles
# ==========================================
@mcp.tool()
def add_image(path: str, image_path: str, width_inches: Optional[float] = None, height_inches: Optional[float] = None) -> str: 
    """ADDS image to doc. [ACTION]
    
    [RAG Context]
    """
    return media_ops.add_image(path, image_path, width_inches, height_inches)

@mcp.tool()
def add_picture_stream(path: str, image_base64: str, width_inches: Optional[float] = None) -> str: 
    """ADDS image from base64. [ACTION]
    
    [RAG Context]
    """
    return media_ops.add_picture_stream(path, image_base64, width_inches)

@mcp.tool()
def get_document_styles(path: str, type_filter: str = "PARAGRAPH") -> List[str]: 
    """LISTS available styles. [DATA]
    
    [RAG Context]
    """
    return style_ops.get_document_styles(path, type_filter)

@mcp.tool()
def apply_paragraph_style(path: str, paragraph_index: int, style_name: str) -> str: 
    """APPLIES style to paragraph. [ACTION]
    
    [RAG Context]
    """
    return style_ops.apply_paragraph_style(path, paragraph_index, style_name)

@mcp.tool()
def create_paragraph_style(path: str, style_name: str, font_name: str = "Arial", font_size: int = 12, base_style: str = "Normal") -> str: 
    """CREATES new style. [ACTION]
    
    [RAG Context]
    """
    return style_ops.create_paragraph_style(path, style_name, font_name, font_size, base_style)

# ==========================================
# 6. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_read_text(path: str) -> str: 
    """READS all text (flat). [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_read_text(path)

@mcp.tool()
def bulk_read_tables(path: str) -> List[List[List[str]]]: 
    """READS all tables (bulk). [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_read_tables(path)

@mcp.tool()
def bulk_replace_text(path: str, replacements: Dict[str, str]) -> int: 
    """REPLACES multiple texts. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_replace_text(path, replacements)

@mcp.tool()
def bulk_add_paragraphs(path: str, paragraphs: List[str], style: str = "Normal") -> str: 
    """ADDS multiple paragraphs. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_add_paragraphs(path, paragraphs, style)

@mcp.tool()
def bulk_add_table_data(path: str, table_index: int, data: List[List[str]]) -> str: 
    """ADDS data to table. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.bulk_add_table_data(path, table_index, data)

@mcp.tool()
def extract_all_images(path: str, output_dir: str) -> List[str]: 
    """EXTRACTS all images to dir. [ACTION]
    
    [RAG Context]
    """
    return bulk_ops.extract_all_images(path, output_dir)

@mcp.tool()
def inspect_document_structure(path: str) -> Dict[str, Any]: 
    """ANALYZES XML structure. [DATA]
    
    [RAG Context]
    Debug low-level structure.
    """
    return super_ops.inspect_document_structure(path)

@mcp.tool()
def create_invoice(path: str, data: Dict[str, Any]) -> str: 
    """CREATES invoice from data. [ACTION]
    
    [RAG Context]
    Uses internal template.
    """
    return super_ops.create_invoice(path, data)

@mcp.tool()
def convert_to_markdown(path: str) -> str: 
    """CONVERTS doc to markdown. [DATA]
    
    [RAG Context]
    """
    return super_ops.convert_to_markdown(path)

@mcp.tool()
def template_fill(template_path: str, output_path: str, replacements: Dict[str, str]) -> str: 
    """FILLS jinja-like template. [ACTION]
    
    [RAG Context]
    Replaces {{key}} placeholders.
    """
    return super_ops.template_fill(template_path, output_path, replacements)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class DocxServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

