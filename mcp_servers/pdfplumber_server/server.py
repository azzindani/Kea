# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "pdfplumber",
#   "pillow",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    core_ops, text_ops, metadata_ops, table_ops, visual_ops, 
    page_ops, bulk_ops, filter_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Union, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("pdfplumber_server", dependencies=["pdfplumber", "pandas", "pillow"])

# ==========================================
# 1. Core & Metadata
# ==========================================
@mcp.tool()
def get_pdf_metadata(path: str) -> dict: return core_ops.get_pdf_metadata(path)
@mcp.tool()
def get_page_count(path: str) -> int: return core_ops.get_page_count(path)
@mcp.tool()
def get_page_dimensions(path: str, page_number: int) -> dict: return core_ops.get_page_dimensions(path, page_number)
@mcp.tool()
def validate_pdf(path: str) -> dict: return core_ops.validate_pdf(path)

# Detailed Metadata
@mcp.tool()
def get_page_resolution(path: str, page_number: int) -> int: return metadata_ops.get_page_resolution(path, page_number)
@mcp.tool()
def get_text_density(path: str, page_number: int) -> float: return metadata_ops.get_text_density(path, page_number)
@mcp.tool()
def inspect_page_objects(path: str, page_number: int) -> dict: return metadata_ops.inspect_page_objects(path, page_number)

# ==========================================
# 2. Text Extraction
# ==========================================
@mcp.tool()
def extract_text_simple(path: str, page_number: int) -> str: return text_ops.extract_text_simple(path, page_number)
@mcp.tool()
def extract_text_layout(path: str, page_number: int, layout: bool = True, x_tolerance: float = 0, y_tolerance: float = 0) -> str: return text_ops.extract_text_layout(path, page_number, layout, x_tolerance, y_tolerance)
@mcp.tool()
def extract_words(path: str, page_number: int, keep_blank_chars: bool = False, x_tolerance: float = 0, y_tolerance: float = 0) -> List[Dict[str, Any]]: return text_ops.extract_words(path, page_number, keep_blank_chars, x_tolerance, y_tolerance)
@mcp.tool()
def extract_chars(path: str, page_number: int) -> List[Dict[str, Any]]: return text_ops.extract_chars(path, page_number)
@mcp.tool()
def extract_text_by_bbox(path: str, page_number: int, bbox: List[Union[int, float]]) -> str: return text_ops.extract_text_by_bbox(path, page_number, bbox)
@mcp.tool()
def search_text(path: str, page_number: int, regex_pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]: return text_ops.search_text(path, page_number, regex_pattern, case_sensitive)
@mcp.tool()
def extract_text_vertical(path: str, page_number: int) -> str: return text_ops.extract_text_vertical(path, page_number)
@mcp.tool()
def extract_text_with_attributes(path: str, page_number: int, font_name: Optional[str] = None, min_size: Optional[float] = None) -> List[str]: return text_ops.extract_text_with_attributes(path, page_number, font_name, min_size)
@mcp.tool()
def extract_sentences(path: str, page_number: int) -> List[str]: return text_ops.extract_sentences(path, page_number)
@mcp.tool()
def extract_paragraphs(path: str, page_number: int) -> List[str]: return text_ops.extract_paragraphs(path, page_number)

# ==========================================
# 3. Table Extraction
# ==========================================
@mcp.tool()
def extract_tables(path: str, page_number: int) -> List[List[List[Optional[str]]]]: return table_ops.extract_tables(path, page_number)
@mcp.tool()
def extract_table_largest(path: str, page_number: int) -> List[List[Optional[str]]]: return table_ops.extract_table_largest(path, page_number)
@mcp.tool()
def extract_tables_json(path: str, page_number: int) -> List[List[Dict[str, Any]]]: return table_ops.extract_tables_json(path, page_number)
@mcp.tool()
def extract_tables_csv(path: str, page_number: int) -> List[str]: return table_ops.extract_tables_csv(path, page_number)
@mcp.tool()
def debug_table_finder(path: str, page_number: int) -> str: return table_ops.debug_table_finder(path, page_number)
@mcp.tool()
def extract_tables_explicit(path: str, page_number: int, vertical_strategy: str = "lines", horizontal_strategy: str = "lines") -> List[List[List[Optional[str]]]]: return table_ops.extract_tables_explicit(path, page_number, vertical_strategy, horizontal_strategy)
@mcp.tool()
def extract_tables_merged(path: str, page_number: int) -> List[List[List[Optional[str]]]]: return table_ops.extract_tables_merged(path, page_number)

# ==========================================
# 4. Visual Elements
# ==========================================
@mcp.tool()
def extract_images(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_images(path, page_number)
@mcp.tool()
def extract_image_metadata(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_image_metadata(path, page_number)
@mcp.tool()
def extract_lines(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_lines(path, page_number)
@mcp.tool()
def extract_rects(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_rects(path, page_number)
@mcp.tool()
def extract_curves(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_curves(path, page_number)
@mcp.tool()
def extract_figures(path: str, page_number: int) -> List[Dict[str, Any]]: return visual_ops.extract_figures(path, page_number)
@mcp.tool()
def render_page_image(path: str, page_number: int, resolution: int = 72) -> str: return visual_ops.render_page_image(path, page_number, resolution)
@mcp.tool()
def render_page_crop(path: str, page_number: int, bbox: List[Union[int, float]], resolution: int = 72) -> str: return visual_ops.render_page_crop(path, page_number, bbox, resolution)

# ==========================================
# 5. Page & Advanced
# ==========================================
@mcp.tool()
def extract_hyperlinks(path: str, page_number: int) -> List[Dict[str, Any]]: return page_ops.extract_hyperlinks(path, page_number)
@mcp.tool()
def extract_annotations(path: str, page_number: int) -> List[Dict[str, Any]]: return page_ops.extract_annotations(path, page_number)
@mcp.tool()
def filter_objects_by_area(path: str, page_number: int, bbox: List[Union[int, float]]) -> Dict[str, int]: return filter_ops.filter_objects_by_area(path, page_number, bbox)
@mcp.tool()
def filter_text_by_font(path: str, page_number: int, font_name_contains: str) -> List[str]: return filter_ops.filter_text_by_font(path, page_number, font_name_contains)

# ==========================================
# 6. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_extract_text(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]: return bulk_ops.bulk_extract_text(path, start_page, end_page)
@mcp.tool()
def bulk_extract_tables(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]: return bulk_ops.bulk_extract_tables(path, start_page, end_page)
@mcp.tool()
def bulk_extract_images(path: str) -> List[Dict[str, Any]]: return bulk_ops.bulk_extract_images(path)
@mcp.tool()
def bulk_search_text(path: str, query: str) -> List[Dict[str, Any]]: return bulk_ops.bulk_search_text(path, query)

@mcp.tool()
def analyze_document_structure(path: str) -> Dict[str, Any]: return super_ops.analyze_document_structure(path)
@mcp.tool()
def auto_extract_all(path: str, page_number: int) -> Dict[str, Any]: return super_ops.auto_extract_all(path, page_number)
@mcp.tool()
def diagnose_pdf(path: str) -> Dict[str, Any]: return super_ops.diagnose_pdf(path)

if __name__ == "__main__":
    mcp.run()
