
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

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
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
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
# ==========================================
# 1. Core & Metadata
# ==========================================
@mcp.tool()
def get_pdf_metadata(path: str) -> dict: 
    """READS PDF metadata keys. [DATA]
    
    [RAG Context]
    Author, Title, etc.
    """
    return core_ops.get_pdf_metadata(path)

@mcp.tool()
def get_page_count(path: str) -> int: 
    """COUNTS pages in PDF. [DATA]
    
    [RAG Context]
    """
    return core_ops.get_page_count(path)

@mcp.tool()
def get_page_dimensions(path: str, page_number: int) -> dict: 
    """GETS page width/height. [DATA]
    
    [RAG Context]
    """
    return core_ops.get_page_dimensions(path, page_number)

@mcp.tool()
def validate_pdf(path: str) -> dict: 
    """VALIDATES PDF structure. [DATA]
    
    [RAG Context]
    Checks for corruption.
    """
    return core_ops.validate_pdf(path)

# Detailed Metadata
@mcp.tool()
def get_page_resolution(path: str, page_number: int) -> int: 
    """GETS page PPI/resolution. [DATA]
    
    [RAG Context]
    """
    return metadata_ops.get_page_resolution(path, page_number)

@mcp.tool()
def get_text_density(path: str, page_number: int) -> float: 
    """CALCULATES text-to-area ratio. [DATA]
    
    [RAG Context]
    Useful for identifying scanned pages.
    """
    return metadata_ops.get_text_density(path, page_number)

@mcp.tool()
def inspect_page_objects(path: str, page_number: int) -> dict: 
    """LISTS all objects on page. [DATA]
    
    [RAG Context]
    Debug tool.
    """
    return metadata_ops.inspect_page_objects(path, page_number)

# ==========================================
# 2. Text Extraction
# ==========================================
@mcp.tool()
def extract_text_simple(path: str, page_number: int) -> str: 
    """EXTRACTS plain text. [DATA]
    
    [RAG Context]
    Fast extraction.
    """
    return text_ops.extract_text_simple(path, page_number)

@mcp.tool()
def extract_text_layout(path: str, page_number: int, layout: bool = True, x_tolerance: float = 0, y_tolerance: float = 0) -> str: 
    """EXTRACTS text preserving layout. [DATA]
    
    [RAG Context]
    Tries to maintain physical layout.
    """
    return text_ops.extract_text_layout(path, page_number, layout, x_tolerance, y_tolerance)

@mcp.tool()
def extract_words(path: str, page_number: int, keep_blank_chars: bool = False, x_tolerance: float = 0, y_tolerance: float = 0) -> List[Dict[str, Any]]: 
    """EXTRACTS words with coords. [DATA]
    
    [RAG Context]
    Returns text and bounding boxes.
    """
    return text_ops.extract_words(path, page_number, keep_blank_chars, x_tolerance, y_tolerance)

@mcp.tool()
def extract_chars(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS characters with coords. [DATA]
    
    [RAG Context]
    Detailed character info.
    """
    return text_ops.extract_chars(path, page_number)

@mcp.tool()
def extract_text_by_bbox(path: str, page_number: int, bbox: List[Union[int, float]]) -> str: 
    """EXTRACTS text from area. [DATA]
    
    [RAG Context]
    bbox: [x0, top, x1, bottom].
    """
    return text_ops.extract_text_by_bbox(path, page_number, bbox)

@mcp.tool()
def search_text(path: str, page_number: int, regex_pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]: 
    """SEARCHES text using regex. [DATA]
    
    [RAG Context]
    Returns matches with coordinates.
    """
    return text_ops.search_text(path, page_number, regex_pattern, case_sensitive)

@mcp.tool()
def extract_text_vertical(path: str, page_number: int) -> str: 
    """EXTRACTS vertical text. [DATA]
    
    [RAG Context]
    """
    return text_ops.extract_text_vertical(path, page_number)

@mcp.tool()
def extract_text_with_attributes(path: str, page_number: int, font_name: Optional[str] = None, min_size: Optional[float] = None) -> List[str]: 
    """EXTRACTS text matching font/size. [DATA]
    
    [RAG Context]
    Filter by visual attributes.
    """
    return text_ops.extract_text_with_attributes(path, page_number, font_name, min_size)

@mcp.tool()
def extract_sentences(path: str, page_number: int) -> List[str]: 
    """EXTRACTS sentences (NLP). [DATA]
    
    [RAG Context]
    """
    return text_ops.extract_sentences(path, page_number)

@mcp.tool()
def extract_paragraphs(path: str, page_number: int) -> List[str]: 
    """EXTRACTS paragraphs. [DATA]
    
    [RAG Context]
    """
    return text_ops.extract_paragraphs(path, page_number)

# ==========================================
# 3. Table Extraction
# ==========================================
# ==========================================
# 3. Table Extraction
# ==========================================
@mcp.tool()
def extract_tables(path: str, page_number: int) -> List[List[List[Optional[str]]]]: 
    """EXTRACTS all tables from page. [DATA]
    
    [RAG Context]
    Returns list of tables, each table is list of rows.
    """
    return table_ops.extract_tables(path, page_number)

@mcp.tool()
def extract_table_largest(path: str, page_number: int) -> List[List[Optional[str]]]: 
    """EXTRACTS largest table. [DATA]
    
    [RAG Context]
    """
    return table_ops.extract_table_largest(path, page_number)

@mcp.tool()
def extract_tables_json(path: str, page_number: int) -> List[List[Dict[str, Any]]]: 
    """EXTRACTS tables as JSON. [DATA]
    
    [RAG Context]
    Rows as dicts with header keys.
    """
    return table_ops.extract_tables_json(path, page_number)

@mcp.tool()
def extract_tables_csv(path: str, page_number: int) -> List[str]: 
    """EXTRACTS tables as CSV string. [DATA]
    
    [RAG Context]
    """
    return table_ops.extract_tables_csv(path, page_number)

@mcp.tool()
def debug_table_finder(path: str, page_number: int) -> str: 
    """GENERATES debug image for tables. [DATA]
    
    [RAG Context]
    Visualizes table detection settings.
    """
    return table_ops.debug_table_finder(path, page_number)

@mcp.tool()
def extract_tables_explicit(path: str, page_number: int, vertical_strategy: str = "lines", horizontal_strategy: str = "lines") -> List[List[List[Optional[str]]]]: 
    """EXTRACTS tables using strategies. [DATA]
    
    [RAG Context]
    Args:
        vertical_strategy: 'lines', 'text', 'gutter'
        horizontal_strategy: 'lines', 'text', 'gutter'
    """
    return table_ops.extract_tables_explicit(path, page_number, vertical_strategy, horizontal_strategy)

@mcp.tool()
def extract_tables_merged(path: str, page_number: int) -> List[List[List[Optional[str]]]]: 
    """EXTRACTS tables handling merged cells. [DATA]
    
    [RAG Context]
    """
    return table_ops.extract_tables_merged(path, page_number)

# ==========================================
# 4. Visual Elements
# ==========================================
# ==========================================
# 4. Visual Elements
# ==========================================
@mcp.tool()
def extract_images(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS images with metadata. [DATA]
    
    [RAG Context]
    """
    return visual_ops.extract_images(path, page_number)

@mcp.tool()
def extract_image_metadata(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS only image metadata. [DATA]
    
    [RAG Context]
    Faster than extracting image data.
    """
    return visual_ops.extract_image_metadata(path, page_number)

@mcp.tool()
def extract_lines(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS vector lines. [DATA]
    
    [RAG Context]
    Useful for table detection.
    """
    return visual_ops.extract_lines(path, page_number)

@mcp.tool()
def extract_rects(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS vector rectangles. [DATA]
    
    [RAG Context]
    """
    return visual_ops.extract_rects(path, page_number)

@mcp.tool()
def extract_curves(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS vector curves. [DATA]
    
    [RAG Context]
    """
    return visual_ops.extract_curves(path, page_number)

@mcp.tool()
def extract_figures(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS combined figures. [DATA]
    
    [RAG Context]
    """
    return visual_ops.extract_figures(path, page_number)

@mcp.tool()
def render_page_image(path: str, page_number: int, resolution: int = 72) -> str: 
    """RENDERS page to image. [DATA]
    
    [RAG Context]
    Returns base64 image.
    """
    return visual_ops.render_page_image(path, page_number, resolution)

@mcp.tool()
def render_page_crop(path: str, page_number: int, bbox: List[Union[int, float]], resolution: int = 72) -> str: 
    """RENDERS cropped area to image. [DATA]
    
    [RAG Context]
    """
    return visual_ops.render_page_crop(path, page_number, bbox, resolution)

# ==========================================
# 5. Page & Advanced
# ==========================================
@mcp.tool()
def extract_hyperlinks(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS hyperlinks. [DATA]
    
    [RAG Context]
    URI and coordinates.
    """
    return page_ops.extract_hyperlinks(path, page_number)

@mcp.tool()
def extract_annotations(path: str, page_number: int) -> List[Dict[str, Any]]: 
    """EXTRACTS annotations/comments. [DATA]
    
    [RAG Context]
    """
    return page_ops.extract_annotations(path, page_number)

@mcp.tool()
def filter_objects_by_area(path: str, page_number: int, bbox: List[Union[int, float]]) -> Dict[str, int]: 
    """COUNTS objects in area. [DATA]
    
    [RAG Context]
    """
    return filter_ops.filter_objects_by_area(path, page_number, bbox)

@mcp.tool()
def filter_text_by_font(path: str, page_number: int, font_name_contains: str) -> List[str]: 
    """FILTERS text by font name. [DATA]
    
    [RAG Context]
    """
    return filter_ops.filter_text_by_font(path, page_number, font_name_contains)

# ==========================================
# 6. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_extract_text(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]: 
    """EXTRACTS text from page range. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_extract_text(path, start_page, end_page)

@mcp.tool()
def bulk_extract_tables(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]: 
    """EXTRACTS tables from page range. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_extract_tables(path, start_page, end_page)

@mcp.tool()
def bulk_extract_images(path: str) -> List[Dict[str, Any]]: 
    """EXTRACTS images from entire PDF. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_extract_images(path)

@mcp.tool()
def bulk_search_text(path: str, query: str) -> List[Dict[str, Any]]: 
    """SEARCHES text in entire PDF. [DATA]
    
    [RAG Context]
    """
    return bulk_ops.bulk_search_text(path, query)

@mcp.tool()
def analyze_document_structure(path: str) -> Dict[str, Any]: 
    """ANALYZES document structure. [DATA]
    
    [RAG Context]
    Heuristic analysis of layout.
    """
    return super_ops.analyze_document_structure(path)

@mcp.tool()
def auto_extract_all(path: str, page_number: int) -> Dict[str, Any]: 
    """EXTRACTS everything from page. [DATA]
    
    [RAG Context]
    Text, tables, images.
    """
    return super_ops.auto_extract_all(path, page_number)

@mcp.tool()
def diagnose_pdf(path: str) -> Dict[str, Any]: 
    """CHECKS PDF health. [DATA]
    
    [RAG Context]
    Metadata, encryption, etc.
    """
    return super_ops.diagnose_pdf(path)

if __name__ == "__main__":
    mcp.run()