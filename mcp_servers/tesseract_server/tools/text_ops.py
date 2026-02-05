from mcp_servers.tesseract_server.tools.core_ops import load_image
import pytesseract
from typing import Optional

def image_to_string(image_input: str, lang: Optional[str] = None, config: str = "") -> str:
    """Extract text from an image."""
    img = load_image(image_input)
    return pytesseract.image_to_string(img, lang=lang, config=config)

def image_to_string_timed(image_input: str, timeout: int = 10) -> str:
    """Extract text with a timeout constraint."""
    img = load_image(image_input)
    # pytesseract supports timeout
    return pytesseract.image_to_string(img, timeout=timeout)
