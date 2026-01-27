from mcp_servers.tesseract_server.tools.text_ops import image_to_string
from typing import Optional

# PSM helper wrappers
def ocr_osd_only(image_input: str) -> str:
    """PSM 0: Orientation and script detection only."""
    return image_to_string(image_input, config="--psm 0")

def ocr_auto_osd(image_input: str) -> str:
    """PSM 1: Automatic page segmentation with OSD."""
    return image_to_string(image_input, config="--psm 1")

def ocr_auto_no_osd(image_input: str) -> str:
    """PSM 3: Fully automatic page segmentation, but no OSD (Default)."""
    return image_to_string(image_input, config="--psm 3")

def ocr_single_column(image_input: str) -> str:
    """PSM 4: Assume a single column of text of variable sizes."""
    return image_to_string(image_input, config="--psm 4")

def ocr_single_block_vert(image_input: str) -> str:
    """PSM 5: Assume a single uniform block of vertically aligned text."""
    return image_to_string(image_input, config="--psm 5")

def ocr_single_block(image_input: str) -> str:
    """PSM 6: Assume a single uniform block of text."""
    return image_to_string(image_input, config="--psm 6")

def ocr_single_line(image_input: str) -> str:
    """PSM 7: Treat the image as a single text line."""
    return image_to_string(image_input, config="--psm 7")

def ocr_single_word(image_input: str) -> str:
    """PSM 8: Treat the image as a single word."""
    return image_to_string(image_input, config="--psm 8")

def ocr_circle_word(image_input: str) -> str:
    """PSM 9: Treat the image as a single word in a circle."""
    return image_to_string(image_input, config="--psm 9")

def ocr_single_char(image_input: str) -> str:
    """PSM 10: Treat the image as a single character."""
    return image_to_string(image_input, config="--psm 10")

def ocr_sparse_text(image_input: str) -> str:
    """PSM 11: Sparse text. Find as much text as possible in no particular order."""
    return image_to_string(image_input, config="--psm 11")

def ocr_sparse_osd(image_input: str) -> str:
    """PSM 12: Sparse text with OSD."""
    return image_to_string(image_input, config="--psm 12")

def ocr_raw_line(image_input: str) -> str:
    """PSM 13: Raw line. Treat the image as a single text line."""
    return image_to_string(image_input, config="--psm 13")
