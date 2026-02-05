from mcp_servers.xmltodict_server.tools import core_ops
from typing import Dict, Any, Optional

def unparse_dict_string(data: Dict[str, Any]) -> str:
    """Dict to XML string."""
    return core_ops._safe_unparse(data)

def unparse_dict_pretty(data: Dict[str, Any]) -> str:
    """Pretty printed XML."""
    return core_ops._safe_unparse(data, pretty=True)

def unparse_dict_no_header(data: Dict[str, Any]) -> str:
    """Omit XML declaration."""
    return core_ops._safe_unparse(data, full_document=False)

def unparse_dict_full_document(data: Dict[str, Any]) -> str:
    """Generic with all standard opts."""
    return core_ops._safe_unparse(data, full_document=True)

def unparse_dict_short_empty(data: Dict[str, Any]) -> str:
    """Short empty elements (<tag/>)."""
    return core_ops._safe_unparse(data, short_empty_elements=True)

def dict_to_soap_envelope(data: Dict[str, Any]) -> str:
    """Wrap dict in SOAP envelope."""
    envelope = {
        "soapenv:Envelope": {
            "@xmlns:soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
            "soapenv:Header": {},
            "soapenv:Body": data
        }
    }
    return core_ops._safe_unparse(envelope, pretty=True)

def dict_to_rss_xml(data: Dict[str, Any]) -> str:
    """Structure dict as RSS."""
    rss = {
        "rss": {
            "@version": "2.0",
            "channel": data
        }
    }
    return core_ops._safe_unparse(rss, pretty=True)

def dict_to_svg_xml(data: Dict[str, Any]) -> str:
    """Structure dict as SVG."""
    svg = {
        "svg": {
            "@xmlns": "http://www.w3.org/2000/svg",
            **data
        }
    }
    return core_ops._safe_unparse(svg, pretty=True)
