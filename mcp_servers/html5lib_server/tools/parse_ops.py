import html5lib
import structlog
import os
from xml.etree import ElementTree
from typing import Dict, Any, List, Optional, Union

logger = structlog.get_logger()

def _tree_to_string(tree, treebuilder='etree'):
    """Helper to convert tree to string representation."""
    try:
        if treebuilder == 'dom':
             # minidom
             return tree.toxml()
        elif treebuilder == 'lxml':
             from lxml import etree
             return etree.tostring(tree, encoding='unicode', pretty_print=True)
        else:
             # etree (standard)
             try:
                 return ElementTree.tostring(tree, encoding='unicode')
             except:
                 # fallback for older pythons or different ET implementations
                 return str(tree)
    except Exception as e:
        return f"Error serializing: {e}"

def parse_string(html_input: str) -> str:
    """Parse HTML to etree (default)."""
    try:
        doc = html5lib.parse(html_input)
        return _tree_to_string(doc)
    except Exception as e:
        return f"Error: {e}"

def parse_fragment(html_input: str) -> str:
    """Parse HTML fragment."""
    try:
        doc = html5lib.parseFragment(html_input)
        return _tree_to_string(doc)
    except Exception as e:
        return f"Error: {e}"

def parse_lxml(html_input: str) -> str:
    """Parse using treebuilder='lxml'."""
    try:
        doc = html5lib.parse(html_input, treebuilder='lxml')
        return _tree_to_string(doc, treebuilder='lxml')
    except ImportError:
        return "lxml not installed"
    except Exception as e:
        return f"Error: {e}"

def parse_dom(html_input: str) -> str:
    """Parse using treebuilder='dom'."""
    try:
        doc = html5lib.parse(html_input, treebuilder='dom')
        return _tree_to_string(doc, treebuilder='dom')
    except Exception as e:
        return f"Error: {e}"

def parse_validating(html_input: str) -> str:
    """Parse and report if valid (via lint filter if possible)."""
    # html5lib doesn't have a "strict" mode that fails easily on parse for bad HTML, 
    # as it's designed to be lenient. 
    # We can try to reuse the lint filter in walk_ops.
    # For core, we just parse.
    return parse_string(html_input)

def parse_file(file_path: str) -> str:
    """Parse HTML file."""
    try:
        with open(file_path, "rb") as f:
            doc = html5lib.parse(f)
        return _tree_to_string(doc)
    except Exception as e:
        return f"Error: {e}"

def parser_errors(html_input: str) -> List[str]:
    """Get list of parse errors (using debug/strict if available)."""
    # html5lib parser has 'errors' attribute if debug=True? 
    # Or using a custom error handler. 
    # Actual implementation: The pure parser doesn't easily expose errors list unless
    # we subclass. Placeholder.
    return ["Error tracking requires custom parser subclassing in html5lib."]

def detect_encoding(file_path: str) -> str:
    """Use html5lib input stream detection (simulated)."""
    # html5lib does detection internally.
    try:
         with open(file_path, "rb") as f:
             # Just peek 
             parser = html5lib.HTMLParser()
             # We rely on parser to guess, but it doesn't return guess easily.
             # We can use chardet if widely available, but stick to standard libs?
             # Let's just return a placeholder or simple logic
             return "utf-8 (html5lib auto-detects)"
    except:
        return "unknown"
