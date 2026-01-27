import pdfplumber
import structlog
from typing import Any, Dict, List, Optional, Union, Generator
from contextlib import contextmanager

logger = structlog.get_logger()

@contextmanager
def open_pdf(path: str) -> Generator[pdfplumber.pdf.PDF, None, None]:
    """
    Context manager to safely open and close PDF files.
    Logs errors and ensures resources are released.
    """
    try:
        with pdfplumber.open(path) as pdf:
            yield pdf
    except Exception as e:
        logger.error("failed_to_open_pdf", path=path, error=str(e))
        raise

def validate_page_number(pdf: pdfplumber.pdf.PDF, page_number: int) -> pdfplumber.page.Page:
    """
    Validates and retrieves a specific page (1-indexed).
    """
    if not (1 <= page_number <= len(pdf.pages)):
        raise IndexError(f"Page number {page_number} is out of range. PDF has {len(pdf.pages)} pages.")
    return pdf.pages[page_number - 1]

def get_pdf_metadata(path: str) -> Dict[str, Any]:
    """Extract metadata from PDF."""
    with open_pdf(path) as pdf:
        return pdf.metadata

def get_page_count(path: str) -> int:
    """Get total number of pages."""
    with open_pdf(path) as pdf:
        pdf_pages = len(pdf.pages)
        if pdf_pages > 1000:
             logger.warning("large_pdf_detected", pages=pdf_pages, path=path)
        return pdf_pages

def get_page_dimensions(path: str, page_number: int) -> Dict[str, float]:
    """Get dimensions of a specific page."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return {"width": page.width, "height": page.height}

def validate_pdf(path: str) -> Dict[str, bool]:
    """Check if PDF is readable and get basic status."""
    try:
        with open_pdf(path) as pdf:
            return {
                "readable": True,
                "encrypted": False, # pdfplumber handles some decryption automatically, checking attribute if needed
                "pages": len(pdf.pages)
            }
    except Exception as e:
        return {"readable": False, "error": str(e)}
