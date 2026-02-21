
import httpx
import os
import io
import json
try:
    from docx import Document
except ImportError:
    Document = None

from shared.logging import get_logger

logger = get_logger(__name__)

async def parse_docx(url: str) -> str:
    """Parse DOCX file."""
    if Document is None:
        return "Error: python-docx is not installed. Word parsing is unavailable."
    try:
        if url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url)
                response.raise_for_status()
                docx_bytes = response.content
        else:
            if not os.path.exists(url):
                return f"Error: File not found at {url}"
            with open(url, "rb") as f:
                docx_bytes = f.read()
        
        doc = Document(io.BytesIO(docx_bytes))
        
        output_data = {
            "source": url,
            "type": "docx",
            "content": []
        }
        
        for para in doc.paragraphs:
            if para.text.strip():
                output_data["content"].append(para.text)
        
        return json.dumps(output_data, indent=2)
        
    except Exception as e:
        logger.error(f"DOCX Parser error: {e}")
        return f"Error: {str(e)}"
