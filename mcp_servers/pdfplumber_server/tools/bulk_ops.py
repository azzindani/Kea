from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
from typing import Dict, Any, List, Optional
from mcp_servers.pdfplumber_server.tools import text_ops, table_ops, visual_ops

def bulk_extract_text(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]:
    """Extract text from a range of pages."""
    results = []
    with open_pdf(path) as pdf:
        total = len(pdf.pages)
        end = end_page if end_page else total
        for i in range(start_page, end + 1):
            page = validate_page_number(pdf, i)
            text = page.extract_text()
            results.append({"page": i, "text": text})
    return results

def bulk_extract_tables(path: str, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict[str, Any]]:
    """Extract tables from a range of pages."""
    results = []
    with open_pdf(path) as pdf:
        total = len(pdf.pages)
        end = end_page if end_page else total
        for i in range(start_page, end + 1):
            page = validate_page_number(pdf, i)
            tables = page.extract_tables()
            results.append({"page": i, "tables": tables})
    return results

def bulk_extract_images(path: str) -> List[Dict[str, Any]]:
    """Extract all images from the entire PDF."""
    results = []
    with open_pdf(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            # We reuse the visual_ops logic but inline basic part to avoid reopening file constantly
            # Actually, to use `visual_ops` we'd reopening file. Here we do it efficiently in one open.
            for img in page.images:
                 results.append({
                     "page": i,
                     "bbox": (img['x0'], img['top'], img['x1'], img['bottom']),
                     "width": img['width'],
                     "height": img['height']
                     # content skipped for bulk to avoid massive payload, usually metadata is enough for bulk
                 })
    return results

def bulk_search_text(path: str, query: str) -> List[Dict[str, Any]]:
    """Search for text across the entire PDF."""
    results = []
    with open_pdf(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if query in text:
                results.append({"page": i, "matches": text.count(query)})
    return results
