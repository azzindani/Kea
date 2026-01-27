import pdfplumber
from typing import Any, Dict, List, Optional, Union
from mcp_servers.pdfplumber_server.tools.core_ops import open_pdf, validate_page_number
import io
import base64

def extract_images(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Extract embedded images as Base64 strings with metadata."""
    results = []
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        for i, img in enumerate(page.images):
            # Accessing the raw image data usually requires extracting bbox and cropping page to_image 
            # OR getting the raw stream if supported. 
            # PDFPlumber 'images' list gives metadata. To get actual image, we often use page.crop(bbox).to_image().
            # However, exact binary extraction is complex. 
            # We will use the visual approach: render the area where the image is.
            bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
            cropped = page.crop(bbox)
            im = cropped.to_image(resolution=150) # moderate resolution
            
            buffer = io.BytesIO()
            im.save(buffer, format="PNG")
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            results.append({
                "bbox": bbox,
                "width": img['width'],
                "height": img['height'],
                "image_data": b64
            })
    return results

def extract_image_metadata(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get metadata of images without downloading content."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.images

def extract_lines(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get all line objects (coordinates)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.lines

def extract_rects(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get all rectangle objects."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.rects

def extract_curves(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Get all curve objects."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.curves

def extract_figures(path: str, page_number: int) -> List[Dict[str, Any]]:
    """Identify potential figures/charts (usually grouped lines/rects)."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        return page.figures

def render_page_image(path: str, page_number: int, resolution: int = 72) -> str:
    """Render full page as Base64 image."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        im = page.to_image(resolution=resolution)
        buffer = io.BytesIO()
        im.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def render_page_crop(path: str, page_number: int, bbox: List[Union[int, float]], resolution: int = 72) -> str:
    """Render specific crop area of a page."""
    with open_pdf(path) as pdf:
        page = validate_page_number(pdf, page_number)
        cropped = page.crop(bbox)
        im = cropped.to_image(resolution=resolution)
        buffer = io.BytesIO()
        im.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
