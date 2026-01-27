from geopy import distance
from typing import Tuple, Dict, Any

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance (km)."""
    # great_circle is faster but spherical
    p1 = (lat1, lon1)
    p2 = (lat2, lon2)
    return distance.great_circle(p1, p2).km

def calculate_geodesic(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Accurate geodesic distance (km) - default for distance.distance."""
    p1 = (lat1, lon1)
    p2 = (lat2, lon2)
    return distance.distance(p1, p2).km

def get_destination_point(lat: float, lon: float, bearing: float, dist_km: float) -> Tuple[float, float]:
    """Start point + distance + bearing -> End point."""
    p1 = distance.distance(kilometers=dist_km).destination((lat, lon), bearing)
    return (p1.latitude, p1.longitude)

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Bearing between two points."""
    # Geopy doesn't have direct bearing func usually, need manual calc or specialized lib
    # But for now, we can implement basic Haversine bearing formula
    import math
    
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    diff_long = math.radians(lon2 - lon1)
    
    x = math.sin(diff_long) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - (math.sin(lat1_r) * math.cos(lat2_r) * math.cos(diff_long))
    
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

def is_within_distance(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool:
    """Check if B is within X km of A."""
    d = calculate_geodesic(lat1, lon1, lat2, lon2)
    return d <= radius_km

def convert_units(km: float, unit: str = "miles") -> float:
    """Help tool (km -> miles, feet)."""
    d = distance.Distance(kilometers=km)
    if unit == "miles": return d.miles
    if unit == "feet": return d.ft
    if unit == "meters": return d.m
    return km

def get_middle_point(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """Geographic midpoint between A and B."""
    # Simple average for small distances, but for better accuracy on sphere..
    # Using simple average is okay for local, but let's use the destination at half distance/bearing?
    # Or strict midpoint
    # Approximation: (lat1+lat2)/2
    return ((lat1+lat2)/2, (lon1+lon2)/2)
