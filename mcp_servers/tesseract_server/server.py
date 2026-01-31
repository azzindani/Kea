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
@mcp.tool()
def get_tesseract_version() -> str: return core_ops.get_tesseract_version()
@mcp.tool()
def get_languages() -> list: return core_ops.get_languages()

# ==========================================
# 2. Text Extraction
# ==========================================
@mcp.tool()
def image_to_string(image_input: str, lang: Optional[str] = None, config: str = "") -> str: return text_ops.image_to_string(image_input, lang, config)
@mcp.tool()
def image_to_string_timed(image_input: str, timeout: int = 10) -> str: return text_ops.image_to_string_timed(image_input, timeout)

# ==========================================
# 3. Specialized Modes
# ==========================================
@mcp.tool()
def ocr_osd_only(image_input: str) -> str: return config_ops.ocr_osd_only(image_input)
@mcp.tool()
def ocr_auto_osd(image_input: str) -> str: return config_ops.ocr_auto_osd(image_input)
@mcp.tool()
def ocr_auto_no_osd(image_input: str) -> str: return config_ops.ocr_auto_no_osd(image_input)
@mcp.tool()
def ocr_single_column(image_input: str) -> str: return config_ops.ocr_single_column(image_input)
@mcp.tool()
def ocr_single_block_vert(image_input: str) -> str: return config_ops.ocr_single_block_vert(image_input)
@mcp.tool()
def ocr_single_block(image_input: str) -> str: return config_ops.ocr_single_block(image_input)
@mcp.tool()
def ocr_single_line(image_input: str) -> str: return config_ops.ocr_single_line(image_input)
@mcp.tool()
def ocr_single_word(image_input: str) -> str: return config_ops.ocr_single_word(image_input)
@mcp.tool()
def ocr_circle_word(image_input: str) -> str: return config_ops.ocr_circle_word(image_input)
@mcp.tool()
def ocr_single_char(image_input: str) -> str: return config_ops.ocr_single_char(image_input)
@mcp.tool()
def ocr_sparse_text(image_input: str) -> str: return config_ops.ocr_sparse_text(image_input)
@mcp.tool()
def ocr_sparse_osd(image_input: str) -> str: return config_ops.ocr_sparse_osd(image_input)
@mcp.tool()
def ocr_raw_line(image_input: str) -> str: return config_ops.ocr_raw_line(image_input)

# ==========================================
# 4. Layout & Boxes
# ==========================================
@mcp.tool()
def get_char_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]: return box_ops.get_char_boxes(image_input, lang)
@mcp.tool()
def get_word_boxes(image_input: str, lang: str = None) -> List[Dict[str, Any]]: return box_ops.get_word_boxes(image_input, lang)
@mcp.tool()
def render_boxes_on_image(image_input: str, level: str = "word") -> str: return box_ops.render_boxes_on_image(image_input, level)

# ==========================================
# 5. Data & Metrics
# ==========================================
@mcp.tool()
def image_to_data_dict(image_input: str, lang: str = None) -> Dict[str, List[Any]]: return data_ops.image_to_data_dict(image_input, lang)
@mcp.tool()
def image_to_data_df(image_input: str, lang: str = None) -> List[Dict[str, Any]]: return data_ops.image_to_data_df(image_input, lang)
@mcp.tool()
def image_to_osd_dict(image_input: str) -> Dict[str, Any]: return data_ops.image_to_osd_dict(image_input)
@mcp.tool()
def get_confidence_score(image_input: str) -> float: return data_ops.get_confidence_score(image_input)
@mcp.tool()
def filter_low_confidence(image_input: str, min_conf: int = 50) -> str: return data_ops.filter_low_confidence(image_input, min_conf)

# ==========================================
# 6. Formats
# ==========================================
@mcp.tool()
def image_to_hocr(image_input: str, lang: str = None) -> str: return format_ops.image_to_hocr(image_input, lang)
@mcp.tool()
def image_to_alto_xml(image_input: str, lang: str = None) -> str: return format_ops.image_to_alto_xml(image_input, lang)
@mcp.tool()
def image_to_tsv(image_input: str, lang: str = None) -> str: return format_ops.image_to_tsv(image_input, lang)
@mcp.tool()
def image_to_pdf(image_input: str, lang: str = None) -> str: return format_ops.image_to_pdf(image_input, lang)
@mcp.tool()
def image_to_xml(image_input: str, lang: str = None) -> str: return format_ops.image_to_xml(image_input, lang)

# ==========================================
# 7. Preprocessing
# ==========================================
@mcp.tool()
def preprocess_grayscale(image_input: str) -> str: return preprocess_ops.preprocess_grayscale(image_input)
@mcp.tool()
def preprocess_threshold(image_input: str, threshold: int = 128) -> str: return preprocess_ops.preprocess_threshold(image_input, threshold)
@mcp.tool()
def preprocess_denoise(image_input: str) -> str: return preprocess_ops.preprocess_denoise(image_input)
@mcp.tool()
def preprocess_invert(image_input: str) -> str: return preprocess_ops.preprocess_invert(image_input)
@mcp.tool()
def preprocess_resize(image_input: str, scale_factor: float = 2.0) -> str: return preprocess_ops.preprocess_resize(image_input, scale_factor)

# ==========================================
# 8. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_ocr_directory(directory: str, lang: str = None) -> List[Dict[str, Any]]: return bulk_ops.bulk_ocr_directory(directory, lang)
@mcp.tool()
def bulk_ocr_list(file_paths: List[str], lang: str = None) -> List[Dict[str, Any]]: return bulk_ops.bulk_ocr_list(file_paths, lang)
@mcp.tool()
def bulk_get_stats(directory: str) -> List[Dict[str, Any]]: return bulk_ops.bulk_get_stats(directory)

@mcp.tool()
def auto_ocr_pipeline(image_input: str) -> Dict[str, Any]: return super_ops.auto_ocr_pipeline(image_input)
@mcp.tool()
def ocr_redact_confidential(image_input: str, regex_pattern: str, redact_color: str = "black") -> str: return super_ops.ocr_redact_confidential(image_input, regex_pattern, redact_color)
@mcp.tool()
def extract_receipt_data(image_input: str) -> Dict[str, Any]: return super_ops.extract_receipt_data(image_input)
@mcp.tool()
def ocr_to_json(image_input: str) -> Dict[str, Any]: return super_ops.ocr_to_json(image_input)
@mcp.tool()
def diagnose_image_quality(image_input: str) -> Dict[str, Any]: return super_ops.diagnose_image_quality(image_input)

if __name__ == "__main__":
    mcp.run()