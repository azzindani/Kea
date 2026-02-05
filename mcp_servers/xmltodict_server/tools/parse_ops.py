from mcp_servers.xmltodict_server.tools import core_ops
from typing import Dict, Any, List, Optional
import xmltodict

def parse_xml_string(xml_input: str) -> Dict[str, Any]:
    """Basic XML string to Dict."""
    return core_ops._safe_parse(xml_input)

def parse_xml_no_attrs(xml_input: str) -> Dict[str, Any]:
    """Parse without attributes (@attr)."""
    return core_ops._safe_parse(xml_input, xml_attribs=False)

def parse_xml_no_namespaces(xml_input: str) -> Dict[str, Any]:
    """Parse, collapsing namespaces."""
    return core_ops._safe_parse(xml_input, process_namespaces=False)

def parse_xml_force_list(xml_input: str, tags: List[str]) -> Dict[str, Any]:
    """Force specific tags to be lists using force_list tuple."""
    return core_ops._safe_parse(xml_input, force_list=tuple(tags))

def parse_xml_force_cdata(xml_input: str) -> Dict[str, Any]:
    """Force CDATA handling (force_cdata=True)."""
    return core_ops._safe_parse(xml_input, force_cdata=True)

def parse_xml_custom_encoding(xml_input: str, encoding: str) -> Dict[str, Any]:
    """Parse with specific encoding."""
    return core_ops._safe_parse(xml_input, encoding=encoding)

def parse_xml_disable_entities(xml_input: str) -> Dict[str, Any]:
    """Disable entity expansion (disable_entities=True)."""
    return core_ops._safe_parse(xml_input, disable_entities=True)

def parse_xml_strip_whitespace(xml_input: str) -> Dict[str, Any]:
    """Strip whitespace (strip_whitespace=True)."""
    return core_ops._safe_parse(xml_input, strip_whitespace=True)

def parse_fragment(xml_fragment: str) -> Dict[str, Any]:
    """Parse XML fragment (wrapped in simulated root)."""
    wrapped = f"<root>{xml_fragment}</root>"
    return core_ops._safe_parse(wrapped)

def get_namespaces(xml_input: str) -> Dict[str, str]:
    """Extract all namespaces from XML string."""
    # xmltodict has process_namespaces=True by default which expands them.
    # To get the map, we parse and inspect `xmlns` attrs manually or use `namespaces` arg?
    # Actually, xmltodict lets you provide a namespace map.
    # To EXTRACT, we might just parse and look for @xmlns keys if namespaces=False
    parsed = core_ops._safe_parse(xml_input, process_namespaces=False)
    namespaces = {}
    
    def _recruit_ns(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.startswith('@xmlns'):
                    namespaces[k] = v
                _recruit_ns(v)
        elif isinstance(d, list):
            for i in d:
                _recruit_ns(i)
                
    _recruit_ns(parsed)
    return namespaces
