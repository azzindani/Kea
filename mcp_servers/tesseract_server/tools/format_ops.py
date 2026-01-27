from mcp_servers.tesseract_server.tools.core_ops import load_image
import pytesseract
import base64

def image_to_hocr(image_input: str, lang: str = None) -> str:
    """Get HOCR (HTML) output."""
    img = load_image(image_input)
    return pytesseract.image_to_pdf_or_hocr(img, lang=lang, extension='hocr').decode('utf-8')

def image_to_alto_xml(image_input: str, lang: str = None) -> str:
    """Get ALTO XML output."""
    img = load_image(image_input)
    return pytesseract.image_to_alto_xml(img, lang=lang).decode('utf-8')

def image_to_tsv(image_input: str, lang: str = None) -> str:
    """Get TSV (tab-separated) output."""
    img = load_image(image_input)
    return pytesseract.image_to_string(img, lang=lang, config="tsv") # tsv config usually built-in or accessible via image_to_data

def image_to_pdf(image_input: str, lang: str = None) -> str:
    """Get Searchable PDF as Base64 string."""
    img = load_image(image_input)
    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, lang=lang, extension='pdf')
    return base64.b64encode(pdf_bytes).decode('utf-8')

def image_to_xml(image_input: str, lang: str = None) -> str:
    """Get standard XML output."""
    img = load_image(image_input)
    # Usually alto is preferred, but raw xml sometimes supported via config
    return pytesseract.image_to_string(img, lang=lang, config="hocr") # HOCR is xml-compliant HTML.
