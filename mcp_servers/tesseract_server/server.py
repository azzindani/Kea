
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "opencv-python",
#   "pandas",
#   "pillow",
#   "pytesseract",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    core_ops, text_ops, config_ops, box_ops, data_ops, format_ops,
    preprocess_ops, bulk_ops, super_ops
)
import structlog
from typing import Optional, List, Dict, Any

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("tesseract_server", dependencies=["pytesseract", "pillow", "pandas", "opencv-python"])

# ==========================================
# 1. Core & Config
# ==========================================
# ==========================================
# 1. Core & Config
# ==========================================
@mcp.tool()
def get_tesseract_version() -> str: 
    """FETCHES version. [ACTION]
    
    [RAG Context]
    Get installed Tesseract version.
    Returns version string.
    """
    return core_ops.get_tesseract_version()

@mcp.tool()
def get_languages() -> list: 
    """FETCHES languages. [ACTION]
    
    [RAG Context]
    Get list of available OCR languages.
    Returns list of strings.
    """
    return core_ops.get_languages()

# ==========================================
# 2. Text Extraction
# ==========================================
@mcp.tool()
def image_to_string(image_input: str, lang: Optional[str] = None, config: str = "") -> str: 
    """EXTRACTS text (OCR). [ACTION]
    
    [RAG Context]
    Convert image to text string.
    Returns string.
    """
    return text_ops.image_to_string(image_input, lang, config)

@mcp.tool()
def image_to_string_timed(image_input: str, timeout: int = 10) -> str: 
    """EXTRACTS text (timed). [ACTION]
    
    [RAG Context]
    Convert image to text with timeout.
    Returns string.
    """
    return text_ops.image_to_string_timed(image_input, timeout)

# ==========================================
# 3. Specialized Modes
# ==========================================
@mcp.tool()
def ocr_osd_only(image_input: str) -> str: 
    """DETECTS orientation/script. [ACTION]
    
    [RAG Context]
    Orientation and Script Detection (OSD) only.
    Returns OSD string.
    """
    return config_ops.ocr_osd_only(image_input)

@mcp.tool()
def ocr_auto_osd(image_input: str) -> str: 
    """EXTRACTS text (Auto+OSD). [ACTION]
    
    [RAG Context]
    Automatic page segmentation with OSD.
    Returns string.
    """
    return config_ops.ocr_auto_osd(image_input)

@mcp.tool()
def ocr_auto_no_osd(image_input: str) -> str: 
    """EXTRACTS text (Auto-OSD). [ACTION]
    
    [RAG Context]
    Automatic page segmentation without OSD.
    Returns string.
    """
    return config_ops.ocr_auto_no_osd(image_input)
@mcp.tool()
def ocr_single_column(image_input: str) -> str: 
    """EXTRACTS single column. [ACTION]
    
    [RAG Context]
    Assume a single column of text of variable sizes.
    Returns string.
    """
    return config_ops.ocr_single_column(image_input)

@mcp.tool()
def ocr_single_block_vert(image_input: str) -> str: 
    """EXTRACTS vertical block. [ACTION]
    
    [RAG Context]
    Assume a single uniform block of vertically aligned text.
    Returns string.
    """
    return config_ops.ocr_single_block_vert(image_input)

@mcp.tool()
def ocr_single_block(image_input: str) -> str: 
    """EXTRACTS single block. [ACTION]
    
    [RAG Context]
    Assume a single uniform block of text.
    Returns string.
    """
    return config_ops.ocr_single_block(image_input)

@mcp.tool()
def ocr_single_line(image_input: str) -> str: 
    """EXTRACTS single line. [ACTION]
    
    [RAG Context]
    Treat the image as a single text line.
    Returns string.
    """
    return config_ops.ocr_single_line(image_input)

@mcp.tool()
def ocr_single_word(image_input: str) -> str: 
    """EXTRACTS single word. [ACTION]
    
    [RAG Context]
    Treat the image as a single word.
    Returns string.
    """
    return config_ops.ocr_single_word(image_input)

@mcp.tool()
def ocr_circle_word(image_input: str) -> str: 
    """EXTRACTS word in circle. [ACTION]
    
    [RAG Context]
    Treat the image as a single word in a circle.
    Returns string.
    """
    return config_ops.ocr_circle_word(image_input)

@mcp.tool()
def ocr_single_char(image_input: str) -> str: 
    """EXTRACTS single char. [ACTION]
    
    [RAG Context]
    Treat the image as a single character.
    Returns string.
    """
    return config_ops.ocr_single_char(image_input)

@mcp.tool()
def ocr_sparse_text(image_input: str) -> str: 
    """EXTRACTS sparse text. [ACTION]
    
    [RAG Context]
    Find as much text as possible in no particular order.
    Returns string.
    """
    return config_ops.ocr_sparse_text(image_input)

@mcp.tool()
def ocr_sparse_osd(image_input: str) -> str: 
    """EXTRACTS sparse text (OSD). [ACTION]
    
    [RAG Context]
    Sparse text with Orientation and Script Detection.
    Returns string.
    """
    return config_ops.ocr_sparse_osd(image_input)

@mcp.tool()
def ocr_raw_line(image_input: str) -> str: 
    """EXTRACTS raw line. [ACTION]
    
    [RAG Context]
    Treat image as a single text line (Raw).
    Returns string.
    """
    return config_ops.ocr_raw_line(image_input)

# ==========================================
# 4. Layout & Boxes
# ==========================================
@mcp.tool()
def get_char_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]: 
    """DETECTS char boxes. [ACTION]
    
    [RAG Context]
    Get bounding boxes for characters.
    Returns list of dicts.
    """
    return box_ops.get_char_boxes(image_input, lang)

@mcp.tool()
def get_word_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]: 
    """DETECTS word boxes. [ACTION]
    
    [RAG Context]
    Get bounding boxes for words.
    Returns list of dicts.
    """
    return box_ops.get_word_boxes(image_input, lang)

@mcp.tool()
def render_boxes_on_image(image_input: str, level: str = "word") -> str: 
    """RENDERS boxes. [ACTION]
    
    [RAG Context]
    Draw bounding boxes on image.
    Returns base64 image string.
    """
    return box_ops.render_boxes_on_image(image_input, level)

# ==========================================
# 5. Data & Metrics
# ==========================================
# ==========================================
# 5. Data & Metrics
# ==========================================
@mcp.tool()
def image_to_data_dict(image_input: str, lang: str = None) -> Dict[str, List[Any]]: 
    """EXTRACTS data dict. [ACTION]
    
    [RAG Context]
    Get comprehensive data (conf, position, etc) as dict.
    Returns JSON dict.
    """
    return data_ops.image_to_data_dict(image_input, lang)

@mcp.tool()
def image_to_data_df(image_input: str, lang: str = None) -> List[Dict[str, Any]]: 
    """EXTRACTS data dataframe. [ACTION]
    
    [RAG Context]
    Get comprehensive data as DataFrame records.
    Returns list of records.
    """
    return data_ops.image_to_data_df(image_input, lang)

@mcp.tool()
def image_to_osd_dict(image_input: str) -> Dict[str, Any]: 
    """EXTRACTS OSD data. [ACTION]
    
    [RAG Context]
    Get Orientation and Script Detection data.
    Returns JSON dict.
    """
    return data_ops.image_to_osd_dict(image_input)

@mcp.tool()
def get_confidence_score(image_input: str) -> float: 
    """CALCULATES confidence. [ACTION]
    
    [RAG Context]
    Get average confidence score for OCR.
    Returns float.
    """
    return data_ops.get_confidence_score(image_input)

@mcp.tool()
def filter_low_confidence(image_input: str, min_conf: int = 50) -> str: 
    """FILTERS low confidence. [ACTION]
    
    [RAG Context]
    Remove text with confidence below threshold.
    Returns filtered string.
    """
    return data_ops.filter_low_confidence(image_input, min_conf)

# ==========================================
# 6. Formats
# ==========================================
@mcp.tool()
def image_to_hocr(image_input: str, lang: str = None) -> str: 
    """CONVERTS to HOCR. [ACTION]
    
    [RAG Context]
    Get HOCR (HTML-like) output.
    Returns HOCR string.
    """
    return format_ops.image_to_hocr(image_input, lang)

@mcp.tool()
def image_to_alto_xml(image_input: str, lang: str = None) -> str: 
    """CONVERTS to ALTO XML. [ACTION]
    
    [RAG Context]
    Get ALTO XML output.
    Returns XML string.
    """
    return format_ops.image_to_alto_xml(image_input, lang)

@mcp.tool()
def image_to_tsv(image_input: str, lang: str = None) -> str: 
    """CONVERTS to TSV. [ACTION]
    
    [RAG Context]
    Get TSV (Tab Separated Values) output.
    Returns TSV string.
    """
    return format_ops.image_to_tsv(image_input, lang)

@mcp.tool()
def image_to_pdf(image_input: str, lang: str = None) -> str: 
    """CONVERTS to PDF. [ACTION]
    
    [RAG Context]
    Get searchable PDF output.
    Returns base64 string.
    """
    return format_ops.image_to_pdf(image_input, lang)

@mcp.tool()
def image_to_xml(image_input: str, lang: str = None) -> str: 
    """CONVERTS to XML. [ACTION]
    
    [RAG Context]
    Get XML output.
    Returns XML string.
    """
    return format_ops.image_to_xml(image_input, lang)

# ==========================================
# 7. Preprocessing
# ==========================================
# ==========================================
# 7. Preprocessing
# ==========================================
@mcp.tool()
def preprocess_grayscale(image_input: str) -> str: 
    """PREPROCESS grayscale. [ACTION]
    
    [RAG Context]
    Convert image to grayscale.
    Returns base64 string.
    """
    return preprocess_ops.preprocess_grayscale(image_input)

@mcp.tool()
def preprocess_threshold(image_input: str, threshold: int = 128) -> str: 
    """PREPROCESS threshold. [ACTION]
    
    [RAG Context]
    Apply binary thresholding.
    Returns base64 string.
    """
    return preprocess_ops.preprocess_threshold(image_input, threshold)

@mcp.tool()
def preprocess_denoise(image_input: str) -> str: 
    """PREPROCESS denoise. [ACTION]
    
    [RAG Context]
    Remove noise from image.
    Returns base64 string.
    """
    return preprocess_ops.preprocess_denoise(image_input)

@mcp.tool()
def preprocess_invert(image_input: str) -> str: 
    """PREPROCESS invert. [ACTION]
    
    [RAG Context]
    Invert image colors.
    Returns base64 string.
    """
    return preprocess_ops.preprocess_invert(image_input)

@mcp.tool()
def preprocess_resize(image_input: str, scale_factor: float = 2.0) -> str: 
    """PREPROCESS resize. [ACTION]
    
    [RAG Context]
    Resize image (scale up/down).
    Returns base64 string.
    """
    return preprocess_ops.preprocess_resize(image_input, scale_factor)

# ==========================================
# 8. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_ocr_directory(directory: str, lang: str = None) -> List[Dict[str, Any]]: 
    """OCR directory. [ACTION]
    
    [RAG Context]
    OCR all images in a directory.
    Returns list of results.
    """
    return bulk_ops.bulk_ocr_directory(directory, lang)

@mcp.tool()
def bulk_ocr_list(file_paths: List[str], lang: str = None) -> List[Dict[str, Any]]: 
    """OCR list. [ACTION]
    
    [RAG Context]
    OCR a list of image file paths.
    Returns list of results.
    """
    return bulk_ops.bulk_ocr_list(file_paths, lang)

@mcp.tool()
def bulk_get_stats(directory: str) -> List[Dict[str, Any]]: 
    """FETCHES OCR stats. [ACTION]
    
    [RAG Context]
    Get OCR statistics for a directory.
    Returns list of stats.
    """
    return bulk_ops.bulk_get_stats(directory)

@mcp.tool()
def auto_ocr_pipeline(image_input: str) -> Dict[str, Any]: 
    """RUNS auto OCR. [ACTION]
    
    [RAG Context]
    Preprocessing + OCR + Postprocessing.
    Returns JSON dict.
    """
    return super_ops.auto_ocr_pipeline(image_input)

@mcp.tool()
def ocr_redact_confidential(image_input: str, regex_pattern: str, redact_color: str = "black") -> str: 
    """REDACTS confidential info. [ACTION]
    
    [RAG Context]
    Redact matches of regex on image.
    Returns base64 string.
    """
    return super_ops.ocr_redact_confidential(image_input, regex_pattern, redact_color)

@mcp.tool()
def extract_receipt_data(image_input: str) -> Dict[str, Any]: 
    """EXTRACTS receipt data. [ACTION]
    
    [RAG Context]
    Extract key-value pairs from receipts.
    Returns JSON dict.
    """
    return super_ops.extract_receipt_data(image_input)

@mcp.tool()
def ocr_to_json(image_input: str) -> Dict[str, Any]: 
    """CONVERTS OCR to JSON. [ACTION]
    
    [RAG Context]
    Get full OCR result as structured JSON.
    Returns JSON dict.
    """
    return super_ops.ocr_to_json(image_input)

@mcp.tool()
def diagnose_image_quality(image_input: str) -> Dict[str, Any]: 
    """DIAGNOSES image quality. [ACTION]
    
    [RAG Context]
    Check orientation, blur, and contrast.
    Returns JSON dict.
    """
    return super_ops.diagnose_image_quality(image_input)

if __name__ == "__main__":
    mcp.run()