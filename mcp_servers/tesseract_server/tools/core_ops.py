import pytesseract
from PIL import Image
import structlog
import os
import io
import base64
from typing import Union, Optional, Any

logger = structlog.get_logger()

# Set tesseract path if needed (Windows often needs explicit path)
# We assume it's in PATH, but we can try to find it or allow env var
# Common Windows installation paths
POSSIBLE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.environ.get("TESSERACT_CMD")
]

for path in POSSIBLE_PATHS:
    if path and os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break

def load_image(image_input: Union[str, bytes]) -> Image.Image:
    """
    Load an image from a file path or Base64 string/bytes.
    """
    try:
        if isinstance(image_input, str):
            if os.path.exists(image_input):
                 return Image.open(image_input)
            else:
                 # Try base64
                 try:
                     image_data = base64.b64decode(image_input)
                     return Image.open(io.BytesIO(image_data))
                 except:
                     raise ValueError(f"Image not found at path and not valid base64: {image_input[:50]}...")
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input))
        else:
             raise ValueError("Unsupported image input type")
    except Exception as e:
        logger.error("failed_to_load_image", error=str(e))
        raise

def get_tesseract_version() -> str:
    try:
        return pytesseract.get_tesseract_version()
    except Exception as e:
        return f"Error: {e}. Ensure Tesseract is installed and in PATH."

def get_languages() -> list:
    try:
        return pytesseract.get_languages()
    except Exception as e:
        logger.error("failed_to_get_languages", error=str(e))
        return []
