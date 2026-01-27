from mcp_servers.docx_server.tools.core_ops import open_document, save_document
import docx
from docx.enum.style import WD_STYLE_TYPE
from typing import List, Any

def get_document_styles(path: str, type_filter: str = "PARAGRAPH") -> List[str]:
    """List available styles in document."""
    doc = open_document(path)
    styles = []
    enum_type = getattr(WD_STYLE_TYPE, type_filter, WD_STYLE_TYPE.PARAGRAPH)
    for s in doc.styles:
        if s.type == enum_type:
            styles.append(s.name)
    return styles

def apply_paragraph_style(path: str, paragraph_index: int, style_name: str) -> str:
    """Apply style to a paragraph."""
    doc = open_document(path)
    if paragraph_index >= len(doc.paragraphs): return "Index out of range."
    doc.paragraphs[paragraph_index].style = style_name
    save_document(doc, path)
    return "Style applied."

def create_paragraph_style(path: str, style_name: str, font_name: str = "Arial", font_size: int = 12, base_style: str = "Normal") -> str:
    """Create (or define if latent) a new paragraph style."""
    doc = open_document(path)
    styles = doc.styles
    if style_name in styles:
        # Update existing
        style = styles[style_name]
    else:
        # Create new
        style = styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles[base_style]
    
    font = style.font
    font.name = font_name
    from docx.shared import Pt
    font.size = Pt(font_size)
    save_document(doc, path)
    return f"Style '{style_name}' created/updated."
