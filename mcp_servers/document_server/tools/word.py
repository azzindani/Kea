
import httpx
import io
import json
from docx import Document
from shared.logging import get_logger

logger = get_logger(__name__)

async def parse_docx(url: str) -> str:
    """Parse DOCX file."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            docx_bytes = response.content
        
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
        
    except ImportError:
        return "python-docx not installed. Run: pip install python-docx"
    except Exception as e:
        logger.error(f"DOCX Parser error: {e}")
        return f"Error: {str(e)}"
