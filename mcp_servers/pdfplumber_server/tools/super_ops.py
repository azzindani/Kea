from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
from typing import Dict, Any, List
import statistics

def analyze_document_structure(path: str) -> Dict[str, Any]:
    """Analyze the overall structure (pages, average text density, object counts)."""
    with open_pdf(path) as pdf:
        page_counts = len(pdf.pages)
        char_counts = [len(p.chars) for p in pdf.pages]
        avg_chars = statistics.mean(char_counts) if char_counts else 0
        return {
            "total_pages": page_counts,
            "avg_chars_per_page": avg_chars,
            "metadata": pdf.metadata,
            "has_forms": bool(pdf.doc.catalog.get('AcroForm'))
        }

def auto_extract_all(path: str, page_number: int) -> Dict[str, Any]:
    """Super tool: Extract everything (text, tables, images) from a page in one go."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return {
            "text": page.extract_text(),
            "tables": page.extract_tables(),
            "images": len(page.images), # Count only for lightweight return
            "hyperlinks": len(page.hyperlinks),
            "dimensions": {"width": page.width, "height": page.height}
        }

def diagnose_pdf(path: str) -> Dict[str, Any]:
    """Diagnose PDF quality and complexity."""
    with open_pdf(path) as pdf:
        pages = pdf.pages[:100000] # Check up to 100K pages
        return {
            "is_scanned_likelihood": any(len(p.chars) < 10 for p in pages), # If few chars, likely scanned image
            "has_text_layer": any(len(p.chars) > 0 for p in pages),
            "encryption": "unknown", # pdfplumber handles transparently
            "generator": pdf.metadata.get('Producer', 'Unknown')
        }
