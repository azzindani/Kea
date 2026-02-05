from mcp_servers.tesseract_server.tools.core_ops import load_image
import pytesseract
import io
import base64
from typing import List, Dict, Any

def get_char_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]:
    """Return characters with bounding box coordinates (x, y, x2, y2)."""
    img = load_image(image_input)
    # image_to_boxes returns string like "T 10 20 30 40 0" (char left bottom right top page)
    # Tesseract 0,0 is bottom-left
    raw = pytesseract.image_to_boxes(img, lang=lang)
    boxes = []
    width, height = img.size
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) >= 6:
            char, x1, y1_bot, x2, y2_bot, page = parts[:6]
            x1, x2 = int(x1), int(x2)
            y1_bot, y2_bot = int(y1_bot), int(y2_bot)
            # Convert to top-left origin
            y1 = height - y2_bot
            y2 = height - y1_bot
            boxes.append({
                "char": char,
                "bbox": [x1, y1, x2, y2],
                "page": int(page)
            })
    return boxes

def get_word_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]:
    """Return words with their bounding box coordinates."""
    img = load_image(image_input)
    # image_to_data is better for words
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
    words = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > -1 and data['text'][i].strip():
            words.append({
                "text": data['text'][i],
                "bbox": [data['left'][i], data['top'][i], 
                         data['left'][i] + data['width'][i], 
                         data['top'][i] + data['height'][i]],
                "conf": data['conf'][i]
            })
    return words

def render_boxes_on_image(image_input: str, level: str = "word") -> str:
    """Return Base64 image with drawn boxes around detected text."""
    img = load_image(image_input)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    if level == "char":
        boxes = get_char_boxes(image_input) # Note: requires reopening or passing img object if optimized
        # Re-using internal logic to avoid reload:
        raw = pytesseract.image_to_boxes(img)
        w, h = img.size
        for line in raw.splitlines():
             b = line.split()
             draw.rectangle(((int(b[1]), h - int(b[4])), (int(b[3]), h - int(b[2]))), outline="red")
    else:
        # words
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > -1:
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                draw.rectangle(((x, y), (x + w, y + h)), outline="green")
                
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
