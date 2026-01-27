import pdfplumber
from typing import Any, Dict, List, Optional, Union
from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
import pandas as pd
import io
import base64

def extract_tables(path: str, page_number: int) -> List[List[List[Optional[str]]]]:
    """Extract all tables from a page as 2D lists."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.extract_tables()

def extract_table_largest(path: str, page_number: int) -> List[List[Optional[str]]]:
    """Extract the largest table on the page (by area)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        tables = page.find_tables()
        if not tables:
            return []
        largest = max(tables, key=lambda t: (t.bbox[2]-t.bbox[0]) * (t.bbox[3]-t.bbox[1]))
        return largest.extract()

def extract_tables_json(path: str, page_number: int) -> List[List[Dict[str, Any]]]:
    """Extract tables as list of JSON records (assumes first row is header)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        tables = page.extract_tables()
        results = []
        for table in tables:
            if not table: continue
            df = pd.DataFrame(table[1:], columns=table[0])
            results.append(df.to_dict(orient='records'))
        return results

def extract_tables_csv(path: str, page_number: int) -> List[str]:
    """Return tables as CSV strings."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        tables = page.extract_tables()
        results = []
        for table in tables:
            if not table: continue
            df = pd.DataFrame(table)
            results.append(df.to_csv(index=False, header=False))
        return results

def debug_table_finder(path: str, page_number: int) -> str:
    """Return Base64 image showing detected table lines for debugging."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        im = page.to_image()
        im.debug_tablefinder()
        
        buffer = io.BytesIO()
        im.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def extract_tables_explicit(path: str, page_number: int, vertical_strategy: str = "lines", horizontal_strategy: str = "lines") -> List[List[List[Optional[str]]]]:
    """Extract tables with explicit definition of strategies."""
    # Strategies: 'lines', 'lines_strict', 'text', 'explicit'
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        settings = {
            "vertical_strategy": vertical_strategy,
            "horizontal_strategy": horizontal_strategy
        }
        return page.extract_tables(table_settings=settings)

def extract_tables_merged(path: str, page_number: int) -> List[List[List[Optional[str]]]]:
    """Attempt to extract tables handling merged cells better (uses 'text' alignment as backup)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        settings = {
            "vertical_strategy": "text", 
            "horizontal_strategy": "text",
            "intersection_y_tolerance": 15
        }
        return page.extract_tables(table_settings=settings)
