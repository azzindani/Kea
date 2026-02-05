from mcp_servers.tesseract_server.tools.core_ops import load_image
from PIL import Image, ImageOps, ImageFilter
import io
import base64

def _img_to_b64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def preprocess_grayscale(image_input: str) -> str:
    """Convert image to grayscale."""
    img = load_image(image_input)
    img = ImageOps.grayscale(img)
    return _img_to_b64(img)

def preprocess_threshold(image_input: str, threshold: int = 128) -> str:
    """Apply binary thresholding."""
    img = load_image(image_input)
    img = ImageOps.grayscale(img)
    img = img.point(lambda p: 255 if p > threshold else 0)
    return _img_to_b64(img)

def preprocess_denoise(image_input: str) -> str:
    """Apply median filter to remove noise."""
    img = load_image(image_input)
    img = img.filter(ImageFilter.MedianFilter())
    return _img_to_b64(img)

def preprocess_invert(image_input: str) -> str:
    """Invert colors (useful for white text on dark background)."""
    img = load_image(image_input)
    if img.mode == 'RGBA':
        r,g,b,a = img.split()
        rgb_image = Image.merge('RGB', (r,g,b))
        inverted_image = ImageOps.invert(rgb_image)
        r2,g2,b2 = inverted_image.split()
        img = Image.merge('RGBA', (r2,g2,b2,a))
    else:
        img = ImageOps.invert(img.convert('RGB'))
    return _img_to_b64(img)

def preprocess_resize(image_input: str, scale_factor: float = 2.0) -> str:
    """Resize image."""
    img = load_image(image_input)
    w, h = img.size
    new_size = (int(w * scale_factor), int(h * scale_factor))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    return _img_to_b64(img)

# Deskew usually requires complex analysis (Hough transform) via OpenCV.
# We'll skip CV2 heavy logic for now to keep it lightweight with Pillow unless critically needed.
