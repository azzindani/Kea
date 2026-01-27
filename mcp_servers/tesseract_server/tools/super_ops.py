from mcp_servers.tesseract_server.tools.core_ops import load_image
from mcp_servers.tesseract_server.tools.preprocess_ops import _img_to_b64
import pytesseract
from PIL import Image, ImageDraw, ImageOps
import re
from typing import Dict, Any, List

def auto_ocr_pipeline(image_input: str) -> Dict[str, Any]:
    """
    Pipeline: 
    1. Detect Script/Orientation (OSD)
    2. Rotate if needed
    3. OCR
    """
    img = load_image(image_input)
    try:
        osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        rotate = osd.get('rotate', 0)
        if rotate != 0:
            img = img.rotate(-rotate, expand=True) # Negative to rotate C
    except:
        pass # OSD failed, proceed with original

    text = pytesseract.image_to_string(img)
    return {
        "text": text,
        "processed_image": _img_to_b64(img)
    }

def ocr_redact_confidential(image_input: str, regex_pattern: str, redact_color: str = "black") -> str:
    """OCR and draw boxes over text matches (Redaction)."""
    img = load_image(image_input)
    draw = ImageDraw.Draw(img)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > -1:
            text = data['text'][i]
            if re.search(regex_pattern, text):
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                draw.rectangle(((x, y), (x + w, y + h)), fill=redact_color)
                
    return _img_to_b64(img)

def extract_receipt_data(image_input: str) -> Dict[str, Any]:
    """Specialized pipeline for receipts (using PSM 4/6)."""
    img = load_image(image_input)
    # Receipts are often single column varying sizes
    text = pytesseract.image_to_string(img, config="--psm 4")
    
    # Simple regex heuristics
    total_match = re.search(r'(?i)total[\s:$]+([\d,]+\.\d{2})', text)
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    
    return {
        "raw_text": text,
        "detected_total": total_match.group(1) if total_match else None,
        "detected_date": date_match.group(1) if date_match else None
    }

def ocr_to_json(image_input: str) -> Dict[str, Any]:
    """Convert OCR layout to hierarchical JSON."""
    img = load_image(image_input)
    df = pytesseract.image_to_data(img, output_type=pytesseract.Output.DATAFRAME)
    # Structure: Page -> Block -> Para -> Line -> Word
    blocks = []
    for block_n, block_grp in df.groupby('block_num'):
        paras = []
        for para_n, para_grp in block_grp.groupby('par_num'):
            lines = []
            for line_n, line_grp in para_grp.groupby('line_num'):
                words = []
                for _, row in line_grp.iterrows():
                    if row['text'] and str(row['text']).strip():
                        words.append({
                            "text": str(row['text']),
                            "conf": row['conf'],
                            "bbox": [row['left'], row['top'], row['width'], row['height']]
                        })
                if words: lines.append({"words": words})
            if lines: paras.append({"lines": lines})
        if paras: blocks.append({"paragraphs": paras})
    return {"blocks": blocks}

def diagnose_image_quality(image_input: str) -> Dict[str, Any]:
    """Check constraints for good OCR."""
    img = load_image(image_input)
    w, h = img.size
    dpi_est = w / 8.5 # Assuming standard letter width, very rough
    
    # Check contrast - simplistic stats
    extrema = img.convert("L").getextrema()
    contrast_range = extrema[1] - extrema[0]
    
    return {
        "dimensions": (w, h),
        "contrast_range": contrast_range,
        "recommendation": "Resize up" if h < 1000 else "Good size" # Tesseract likes ~300 DPI, so ~3300px height for Letter
    }
