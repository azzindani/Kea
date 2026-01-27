import html5lib
from html5lib import serializer, treewalkers
from typing import Dict, Any, List

def serialize_tree(html_input: str) -> str:
    """Convert tree (etree) to HTML string."""
    try:
        doc = html5lib.parse(html_input)
        s = serializer.HTMLSerializer()
        walker = treewalkers.getTreeWalker("etree")
        return s.render(walker(doc))
    except Exception as e:
        return f"Error: {e}"

def serialize_minidom(html_input: str) -> str:
    """Convert DOM tree to HTML string."""
    try:
        # Parse to DOM first
        doc = html5lib.parse(html_input, treebuilder="dom")
        s = serializer.HTMLSerializer()
        walker = treewalkers.getTreeWalker("dom")
        return s.render(walker(doc))
    except Exception as e:
        return f"Error: {e}"

def serialize_pretty(html_input: str) -> str:
    """Formatted HTML (if supported or manual indent)."""
    # html5lib default serializer doesn't strictly "pretty print" indentation like lxml.
    # We can rely on lxml backend for this feature if desired, or just standard serialization.
    # Plan mentioned using features if available.
    try:
        # Fallback to lxml for pretty print which is better at it.
        # But we must stay within html5lib logic if possible.
        # html5lib serializer options: quote_attr_values, quote_char, use_best_quote_char, etc.
        # No built-in indent.
        # Use lxml for pretty print power.
        from lxml import etree
        doc = html5lib.parse(html_input, treebuilder='lxml')
        return etree.tostring(doc, encoding='unicode', pretty_print=True)
    except:
        return serialize_tree(html_input) # Fallback

def serialize_no_whitespace(html_input: str) -> str:
    """Strip whitespace during serialization."""
    try:
        doc = html5lib.parse(html_input)
        s = serializer.HTMLSerializer(strip_whitespace=True)
        walker = treewalkers.getTreeWalker("etree")
        return s.render(walker(doc))
    except Exception as e:
        return f"Error: {e}"

def serialize_inject_meta(html_input: str) -> str:
    """Inject meta tags during serialize."""
    try:
        doc = html5lib.parse(html_input)
        s = serializer.HTMLSerializer(inject_meta_charset=True)
        walker = treewalkers.getTreeWalker("etree")
        return s.render(walker(doc))
    except Exception as e:
        return f"Error: {e}"

def reencode_html(html_input: str, encoding: str) -> str:
    """Parse then serialize with new encoding (returns unicode string representation still)."""
    # HTMLSerializer produces unicode string usually.
    # If we want bytes, we encode. 
    # For MCP text tools, we return string.
    # This might be more about injecting the right meta charset?
    return serialize_inject_meta(html_input)
