import httpx
import fitz # PyMuPDF
import json
from shared.logging.structured import get_logger

logger = get_logger(__name__)

async def parse_pdf(url: str, pages: str = "all", extract_tables: bool = False) -> str:
    """
    Parse PDF file.
    pages: 'all', '1-5', '1,3,5'
    """
    try:
        # Download PDF
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            pdf_bytes = response.content
            
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        output_data = {
            "source": url,
            "pages_count": doc.page_count,
            "content": []
        }
        
        # Parse page range
        if pages == "all":
            page_nums = range(doc.page_count)
        elif "-" in pages:
            start, end = pages.split("-")
            page_nums = range(int(start)-1, int(end))
        elif "," in pages:
            page_nums = [int(p)-1 for p in pages.split(",")]
        else:
            page_nums = [int(pages)-1]
        
        for i in page_nums:
            if i < doc.page_count:
                page = doc[i]
                text = page.get_text()
                page_data = {
                    "page": i + 1,
                    "text": text
                }
                output_data["content"].append(page_data)
        
        doc.close()
        return json.dumps(output_data, indent=2)
        
    except ImportError:
        return "pymupdf not installed. Run: pip install pymupdf"
    except Exception as e:
        logger.error(f"PDF Parser error: {e}")
        return f"Error: {str(e)}"
