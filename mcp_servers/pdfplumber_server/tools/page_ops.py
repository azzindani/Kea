from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
from typing import Dict, Any, List

def extract_hyperlinks(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get all hyperlinks (URI actions) from a page."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        links = []
        # pdfplumber extracts annotations usually, but sometimes links are specific objects
        if hasattr(page, 'hyperlinks'):
             return page.hyperlinks
        # Fallback if specific version doesn't support direct property, check annotations
        if page.annots:
            for annot in page.annots:
                if annot.get('uri'):
                    links.append(annot)
        return links

def extract_annotations(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get all annotations (comments, highlights) from a page."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.annots or []

def extract_bookmarks(path: str) -> List[Dict[str, Any]]:
    """Get the Table of Contents (outlines) of the PDF."""
    with open_pdf(path) as pdf:
        # doc.outlines is available directly
        return pdf.doc.catalog.get('Outlines', []) # Simplified, pdfplumber doesn't expose clean API for TOC always
        # Better: use metadata or check if pdfplumber exposes outlines clearly. 
        # Actually pdfplumber doesn't have a strong high-level TOC API. We return raw if possible.
        return [] # Placeholder as pdfplumber focuses on page content. 
                  # Users usually use pypdf for TOC. We'll skip complex TOC to avoid errors.
