from mcp_servers.tesseract_server.tools.core_ops import load_image
import pytesseract
import os
from typing import List, Dict, Any

def bulk_ocr_directory(directory: str, lang: str = None) -> List[Dict[str, Any]]:
    """OCR all images in a directory."""
    results = []
    if not os.path.exists(directory): return []
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            path = os.path.join(directory, filename)
            try:
                text = pytesseract.image_to_string(path, lang=lang)
                results.append({"filename": filename, "text": text})
            except Exception as e:
                results.append({"filename": filename, "error": str(e)})
    return results

def bulk_ocr_list(file_paths: List[str], lang: str = None) -> List[Dict[str, Any]]:
    """OCR a list of image paths."""
    results = []
    for path in file_paths:
        try:
            text = pytesseract.image_to_string(path, lang=lang)
            results.append({"path": path, "text": text})
        except Exception as e:
            results.append({"path": path, "error": str(e)})
    return results

# Requires pdf2image usually, skipping heavy dependency logic for now or keeping simple
# We will focus on image bulk. 

def bulk_get_stats(directory: str) -> List[Dict[str, Any]]:
    """Get stats (confidence, word count) for images in directory."""
    results = []
    if not os.path.exists(directory): return []
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            path = os.path.join(directory, filename)
            try:
                data = pytesseract.image_to_data(path, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data['conf'] if int(c) != -1]
                avg_conf = sum(confs)/len(confs) if confs else 0
                results.append({
                    "filename": filename,
                    "avg_confidence": avg_conf,
                    "word_count": len(confs)
                })
            except Exception as e:
                results.append({"filename": filename, "error": str(e)})
    return results
