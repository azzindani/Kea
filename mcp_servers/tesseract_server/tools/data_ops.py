from mcp_servers.tesseract_server.tools.core_ops import load_image
import pytesseract
from typing import Dict, Any, List
import pandas as pd

def image_to_data_dict(image_input: str, lang: str = None) -> Dict[str, List[Any]]:
    """Return raw data dictionary from Tesseract."""
    img = load_image(image_input)
    return pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

def image_to_data_df(image_input: str, lang: str = None) -> List[Dict[str, Any]]:
    """Return detailed OCR data as a list of records (DataFrame-like)."""
    img = load_image(image_input)
    df = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DATAFRAME)
    # Filter empty text rows usually
    df = df[df.text.notna()]
    return df.to_dict(orient='records')

def image_to_osd_dict(image_input: str) -> Dict[str, Any]:
    """Orientation and script detection details."""
    img = load_image(image_input)
    try:
        return pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError:
        return {"error": "OSD failed (too few characters?)"}

def get_confidence_score(image_input: str) -> float:
    """Get average confidence score of the OCR result."""
    data = image_to_data_dict(image_input)
    confs = [int(c) for c in data['conf'] if int(c) != -1]
    if not confs: return 0.0
    return sum(confs) / len(confs)

def filter_low_confidence(image_input: str, min_conf: int = 50) -> str:
    """Return text only where confidence is above threshold."""
    data = image_to_data_dict(image_input)
    text = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) >= min_conf:
             if(data['text'][i].strip()):
                text.append(data['text'][i])
             else:
                text.append(" ") # Preserve some spacing
        elif int(data['conf'][i]) > -1:
             # Low confidence text, skip or replace?
             pass 
    return "".join(text) # Simple join, layout lossy
