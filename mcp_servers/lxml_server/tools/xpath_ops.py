from lxml import etree, html, cssselect
from typing import List, Dict, Any, Union
from mcp_servers.lxml_server.tools import core_ops

def xpath_query(xml_input: str, query: str) -> List[str]:
    """Run XPath 1.0 query. Returns list of matches as strings."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        results = root.xpath(query)
        # Convert results to strings
        output = []
        for r in results:
            output.append(core_ops._elem_to_str(r))
        return output
    except Exception as e:
        return [f"Error: {e}"]

def xpath_query_text(xml_input: str, query: str) -> List[str]:
    """Get text results directly (e.g. //title/text())."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        results = root.xpath(query)
        # Results might be _ElementUnicodeResult (strings) or Elements
        output = []
        for r in results:
            if isinstance(r, (str, bytes)):
                output.append(str(r))
            elif hasattr(r, 'text'):
                output.append(r.text if r.text else "")
            else:
                output.append(str(r))
        return output
    except Exception as e:
        return [f"Error: {e}"]

def xpath_query_attr(xml_input: str, query: str) -> List[str]:
    """Get attribute values directly (usually via XPath like @href)."""
    # Same as text basically, xpath handles @attr
    return xpath_query_text(xml_input, query)

def css_select(xml_input: str, selector: str) -> List[str]:
    """Select elements using CSS selectors (needs cssselect)."""
    try:
        root = html.fromstring(xml_input) # CSS mostly for HTML
        results = root.cssselect(selector)
        return [core_ops._elem_to_str(r) for r in results]
    except Exception as e:
        return [f"Error: {e}"]

def get_parent(xml_input: str, xpath: str) -> str:
    """Get parent of element found by xpath."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        res = root.xpath(xpath)
        if not res: return "Element not found"
        el = res[0]
        parent = el.getparent()
        return core_ops._elem_to_str(parent) if parent is not None else "No parent (Root)"
    except Exception as e:
        return f"Error: {e}"

def get_children(xml_input: str, xpath: str) -> List[str]:
    """Get children list."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        res = root.xpath(xpath)
        if not res: return []
        el = res[0]
        return [core_ops._elem_to_str(c) for c in el]
    except Exception as e:
        return [f"Error: {e}"]

def get_siblings(xml_input: str, xpath: str) -> Dict[str, str]:
    """Get next/prev siblings."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        res = root.xpath(xpath)
        if not res: return {}
        el = res[0]
        return {
            "prev": core_ops._elem_to_str(el.getprevious()),
            "next": core_ops._elem_to_str(el.getnext())
        }
    except Exception as e:
        return {"error": str(e)}
