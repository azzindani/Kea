import xmltodict
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

def _safe_parse(xml_input: str, **kwargs) -> Dict[str, Any]:
    """Safe wrapper for xmltodict.parse."""
    try:
        if not xml_input.strip():
            return {}
        return xmltodict.parse(xml_input, **kwargs)
    except Exception as e:
        logger.error("parse_error", error=str(e))
        return {"error": str(e)}

def _safe_unparse(dict_input: Dict[str, Any], **kwargs) -> str:
    """Safe wrapper for xmltodict.unparse."""
    try:
        return xmltodict.unparse(dict_input, **kwargs)
    except Exception as e:
        logger.error("unparse_error", error=str(e))
        return f"Error: {e}"
