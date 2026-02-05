import geopy
from geopy.geocoders import Nominatim, GoogleV3, Bing
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

# Global config
CONFIG = {
    "service": "nominatim",
    "user_agent": "kea_research_engine_mcp",
    "api_key": None,
    "timeout": 10
}

# Cache for geocoder instance
_GEOCODER = None

def get_geocoder():
    """Get or create singleton geocoder instance based on config."""
    global _GEOCODER
    # Re-create if config changed implies we might want to force check, but simple singleton is ok for now. 
    # Actually, we should recreate if settings change.
    
    if _GEOCODER: return _GEOCODER
    
    service = CONFIG["service"].lower()
    ua = CONFIG["user_agent"]
    key = CONFIG["api_key"]
    timeout = CONFIG["timeout"]
    
    if service == "nominatim":
        _GEOCODER = Nominatim(user_agent=ua, timeout=timeout)
    elif service == "googlev3":
        if not key: raise ValueError("GoogleV3 requires API key")
        _GEOCODER = GoogleV3(api_key=key, timeout=timeout)
    elif service == "bing":
         if not key: raise ValueError("Bing requires API key")
         _GEOCODER = Bing(api_key=key, timeout=timeout)
    else:
        # Fallback to Nominatim
        _GEOCODER = Nominatim(user_agent=ua, timeout=timeout)
        
    return _GEOCODER

def reset_geocoder():
    """Force re-initialization."""
    global _GEOCODER
    _GEOCODER = None

def get_version() -> str:
    """Return geopy version."""
    return geopy.__version__

def set_user_agent(ua: str) -> str:
    """Custom UA for Nominatim."""
    CONFIG["user_agent"] = ua
    reset_geocoder()
    return f"User Agent set to {ua}"

def set_geocoder_service(service: str) -> str:
    """Switch service (nominatim, googlev3, bing)."""
    if service.lower() not in ["nominatim", "googlev3", "bing"]:
        return "Error: Supported services are nominatim, googlev3, bing"
    CONFIG["service"] = service.lower()
    reset_geocoder()
    return f"Service switched to {service}"

def set_api_key(key: str) -> str:
    """Set key for paid services."""
    CONFIG["api_key"] = key
    reset_geocoder()
    return "API Key updated"

def set_timeout(seconds: int) -> str:
    """Configure request timeout."""
    CONFIG["timeout"] = seconds
    reset_geocoder()
    return f"Timeout set to {seconds}s"
