from mcp_servers.geopy_server.tools import core_ops
from typing import Dict, Any, List, Optional, Tuple, Union

# Helper
def _serialize_location(loc) -> Dict[str, Any]:
    if not loc: return {}
    return {
        "address": loc.address,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "altitude": loc.altitude,
        "raw": loc.raw
    }

def geocode_address(query: str) -> Dict[str, Any]:
    """Address to (Lat, Lon, Full Address)."""
    geolocator = core_ops.get_geocoder()
    try:
        loc = geolocator.geocode(query)
        return _serialize_location(loc)
    except Exception as e:
        return {"error": str(e)}

def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """(Lat, Lon) to Address."""
    geolocator = core_ops.get_geocoder()
    try:
        # string "lat, lon" or tuple (lat, lon)
        loc = geolocator.reverse((lat, lon))
        return _serialize_location(loc)
    except Exception as e:
        return {"error": str(e)}

def get_coordinates(query: str) -> Tuple[float, float]:
    """Just Lat/Lon tuple."""
    res = geocode_address(query)
    if "latitude" in res:
        return (res["latitude"], res["longitude"])
    return (0.0, 0.0)

def get_full_address(lat: float, lon: float) -> str:
    """Just standardized address string."""
    res = reverse_geocode(lat, lon)
    return res.get("address", "Unknown")

def get_altitude(query: str) -> float:
    """Altitude (if supported/available)."""
    res = geocode_address(query)
    return res.get("altitude", 0.0)

def get_zipcode(lat: float, lon: float) -> str:
    """Extract postal code from result."""
    res = reverse_geocode(lat, lon)
    raw = res.get("raw", {})
    address = raw.get("address", {})
    return address.get("postcode", "Unknown")

def get_country(lat: float, lon: float) -> str:
    """Extract country."""
    res = reverse_geocode(lat, lon)
    raw = res.get("raw", {})
    address = raw.get("address", {})
    return address.get("country", "Unknown")

def get_city(lat: float, lon: float) -> str:
    """Extract city."""
    res = reverse_geocode(lat, lon)
    raw = res.get("raw", {})
    address = raw.get("address", {})
    # Nominatim fields vary: city, town, village, hamlet
    return address.get("city") or address.get("town") or address.get("village") or "Unknown"

def get_raw_info(query: str) -> Dict[str, Any]:
    """Return full raw JSON from provider."""
    res = geocode_address(query)
    return res.get("raw", {})

def geocode_with_box(query: str, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> Dict[str, Any]:
    """Bounding box bias."""
    # viewbox argument in Nominatim
    # (min_lat, min_lon), (max_lat, max_lon)
    # Geopy expects viewbox as list of points or something similar depending on provider
    # nominatim.geocode(query, viewbox=[(min_lat, min_lon), (max_lat, max_lon)])
    # or bounded=True
    geolocator = core_ops.get_geocoder()
    try:
        if core_ops.CONFIG["service"] == "nominatim":
             loc = geolocator.geocode(query, viewbox=[(min_lat, min_lon), (max_lat, max_lon)], bounded=True)
             return _serialize_location(loc)
        else:
            return geocode_address(query) # fallback
    except Exception as e:
        return {"error": str(e)}

def geocode_structured(street: str = "", city: str = "", country: str = "") -> Dict[str, Any]:
    """Dict input (street, city, etc.)."""
    # structured query supported by Nominatim
    geolocator = core_ops.get_geocoder()
    query = {}
    if street: query["street"] = street
    if city: query["city"] = city
    if country: query["country"] = country
    
    try:
        if core_ops.CONFIG["service"] == "nominatim":
            loc = geolocator.geocode(query)
            return _serialize_location(loc)
        else:
            # Join as string for others
            q_str = f"{street} {city} {country}".strip()
            return geocode_address(q_str)
    except Exception as e:
        return {"error": str(e)}
