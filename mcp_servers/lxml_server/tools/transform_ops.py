from lxml import etree, html
import structlog
from typing import Dict, Any, List, Optional
from mcp_servers.lxml_server.tools import core_ops
from lxml.builder import E

def xslt_transform(xml_input: str, xslt_input: str) -> str:
    """Apply XSLT 1.0 stylesheet."""
    try:
        dom = etree.fromstring(xml_input.encode('utf-8'))
        xslt = etree.fromstring(xslt_input.encode('utf-8'))
        transform = etree.XSLT(xslt)
        new_dom = transform(dom)
        return core_ops._elem_to_str(new_dom, pretty=True)
    except Exception as e:
        return f"Error: {e}"

def clean_html(html_input: str) -> str:
    """Sanitize HTML (remove scripts/styles) using `lxml.html.clean`."""
    try:
        from lxml.html.clean import Cleaner
        cleaner = Cleaner(style=True, scripts=True, javascript=True, comments=True)
        return cleaner.clean_html(html_input)
    except ImportError:
        return "lxml.html.clean not available (install lxml[html_clean])"
    except Exception as e:
        return f"Error: {e}"

def make_links_absolute(html_input: str, base_url: str) -> str:
    """Rewrite relative links to absolute."""
    try:
        root = html.fromstring(html_input)
        root.make_links_absolute(base_url)
        return core_ops._elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"

def remove_javascript(html_input: str) -> str:
    """Specific script removal."""
    from lxml.html.clean import Cleaner
    cleaner = Cleaner(javascript=True, scripts=True)
    return cleaner.clean_html(html_input)

def builder_create(tag: str, text: str, **attrs) -> str:
    """Create structure using E-builder (simple single element)."""
    try:
        # E.tag(text, **attrs)
        # Dynamic E usage
        factory = getattr(E, tag)
        el = factory(text, **attrs)
        return core_ops._elem_to_str(el, pretty=True)
    except Exception as e:
        return f"Error: {e}"

def add_child(xml_input: str, parent_xpath: str, child_tag: str, child_text: str) -> str:
    """Append child to element."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        parents = root.xpath(parent_xpath)
        if not parents: return "Parent not found"
        p = parents[0]
        child = etree.SubElement(p, child_tag)
        child.text = child_text
        return core_ops._elem_to_str(root, pretty=True)
    except Exception as e:
        return f"Error: {e}"

def set_attribute(xml_input: str, xpath: str, key: str, value: str) -> str:
    """Set/Update attribute."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        target = root.xpath(xpath)
        if not target: return "Target not found"
        target[0].set(key, value)
        return core_ops._elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"

def remove_attribute(xml_input: str, xpath: str, key: str) -> str:
    """Remove attribute."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        target = root.xpath(xpath)
        if not target: return "Target not found"
        if key in target[0].attrib:
            del target[0].attrib[key]
        return core_ops._elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"

def replace_element(xml_input: str, xpath: str, new_tag: str) -> str:
    """Rename tag."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        target = root.xpath(xpath)
        if not target: return "Target not found"
        target[0].tag = new_tag
        return core_ops._elem_to_str(root)
    except Exception as e:
        return f"Error: {e}"
