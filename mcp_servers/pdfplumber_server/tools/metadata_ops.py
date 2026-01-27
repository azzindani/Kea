from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
from typing import Dict, Any

def get_page_resolution(path: str, page_number: int) -> int:
    """Estimate page resolution/DPI based on image objects (heuristic) or return default."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        # PDF pages don't strictly have DPI, but we can return dimensions relative to 72 pt/inch
        # Standard PDF point is 1/72 inch.
        return 72 

def get_text_density(path: str, page_number: int) -> float:
    """Calculate ratio of text area to page area (0.0 to 1.0)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        text_area = 0.0
        for char in page.chars:
            text_area += char.get('width', 0) * char.get('height', 0)
        page_area = page.width * page.height
        return text_area / page_area if page_area > 0 else 0.0

def inspect_page_objects(path: str, page_number: int) -> Dict[str, int]:
    """Count number of objects of each type (chars, lines, rects, curves, images)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return {
            "chars": len(page.chars),
            "lines": len(page.lines),
            "rects": len(page.rects),
            "curves": len(page.curves),
            "images": len(page.images),
            "tables": len(page.find_tables())
        }
