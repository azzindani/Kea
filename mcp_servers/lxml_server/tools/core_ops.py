from lxml import etree, html
import structlog
import os
from typing import Dict, Any, List, Optional, Union

logger = structlog.get_logger()

# Helper to serialize Element to string for response
def _elem_to_str(elem: Union[etree._Element, str], pretty: bool = False) -> str:
    if isinstance(elem, str): return elem # XPath text result
    if elem is None: return ""
    try:
        # If it's HTML, use html.tostring
        if isinstance(elem, html.HtmlElement):
             return html.tostring(elem, pretty_print=pretty, encoding='unicode')
        return etree.tostring(elem, pretty_print=pretty, encoding='unicode')
    except Exception as e:
        return f"Error serializing: {e}"

def parse_xml_string(xml_input: str) -> str:
    """Parse XML string. Returns status (Element is internal object)."""
    try:
        etree.fromstring(xml_input.encode('utf-8'))
        return "Parsed successfully"
    except Exception as e:
        return f"Error: {e}"

def parse_html_string(html_input: str) -> str:
    """Parse HTML string."""
    try:
        html.fromstring(html_input)
        return "Parsed successfully"
    except Exception as e:
        return f"Error: {e}"

def parse_file(file_path: str) -> str:
    """Parse XML/HTML file."""
    try:
        if not os.path.exists(file_path): return "File not found"
        # Try parse
        etree.parse(file_path)
        return "Parsed successfully"
    except Exception as e:
        return f"Error: {e}"

def parse_xml_recover(xml_input: str) -> str:
    """Parse broken XML with recovery mode."""
    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(xml_input, parser)
        return _elem_to_str(root, pretty=True)
    except Exception as e:
        return f"Error: {e}"

def to_string(xml_input: str) -> str:
    """Normalize/Echo XML string (validate & serialize)."""
    try:
        root = etree.fromstring(xml_input)
        return etree.tostring(root, encoding='unicode')
    except Exception as e:
        return f"Error: {e}"

def to_pretty_string(xml_input: str) -> str:
    """Pretty print."""
    try:
        root = etree.fromstring(xml_input)
        return etree.tostring(root, pretty_print=True, encoding='unicode')
    except Exception as e:
        # Fallback to HTML parser if XML fails?
        try:
             root = html.fromstring(xml_input)
             return html.tostring(root, pretty_print=True, encoding='unicode')
        except:
             return f"Error: {e}"

def strip_tags(xml_input: str, tags: List[str]) -> str:
    """Remove specific tags but keep content (strip_tags)."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        etree.strip_tags(root, *tags)
        return _elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"

def strip_elements(xml_input: str, tags: List[str]) -> str:
    """Remove tags and content (strip_elements)."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        etree.strip_elements(root, *tags, with_tail=False)
        return _elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"

def get_element_text(xml_input: str, xpath: str = ".") -> str:
    """Get text content of element (root or specific xpath)."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        # If xpath provided, find first
        if xpath != ".":
            res = root.xpath(xpath)
            if not res: return ""
            target = res[0]
        else:
            target = root
            
        if isinstance(target, str): return target
        return "".join(target.itertext())
    except Exception as e:
        return f"Error: {e}"

def get_element_attrs(xml_input: str, xpath: str = ".") -> Dict[str, str]:
    """Get attributes dictionary."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        if xpath != ".":
            res = root.xpath(xpath)
            if not res: return {}
            target = res[0]
        else:
            target = root
            
        if not isinstance(target, etree._Element): return {}
        return dict(target.attrib)
    except Exception as e:
        return {"error": str(e)}
