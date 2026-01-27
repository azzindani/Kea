from typing import List, Dict, Any, Tuple
from mcp_servers.geopy_server.tools import geocode_ops, distance_ops
import time

def bulk_geocode(queries: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
    """List of addresses -> List of coords. Respects delay."""
    results = []
    for q in queries:
        try:
            res = geocode_ops.geocode_address(q)
            results.append({"query": q, "result": res})
        except Exception as e:
            results.append({"query": q, "error": str(e)})
        time.sleep(delay) # Be polite to Nominatim
    return results

def bulk_reverse(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[Dict[str, Any]]:
    """List of (lat, lon) -> List of addresses."""
    results = []
    for lat, lon in coords:
        try:
            res = geocode_ops.reverse_geocode(lat, lon)
            results.append({"lat": lat, "lon": lon, "result": res})
        except Exception as e:
             results.append({"lat": lat, "lon": lon, "error": str(e)})
        time.sleep(delay)
    return results

def calculate_distance_matrix(locations: List[Tuple[float, float]]) -> List[List[float]]:
    """NxN distance table (km) for list of points."""
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j: continue
            dist = distance_ops.calculate_geodesic(locations[i][0], locations[i][1], locations[j][0], locations[j][1])
            matrix[i][j] = dist
    return matrix

def find_nearest(target_lat: float, target_lon: float, candidates: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Find closest point in List L to Point P."""
    if not candidates: return {}
    best_dist = float('inf')
    best_pt = None
    best_idx = -1
    
    for idx, (lat, lon) in enumerate(candidates):
        d = distance_ops.calculate_geodesic(target_lat, target_lon, lat, lon)
        if d < best_dist:
            best_dist = d
            best_pt = (lat, lon)
            best_idx = idx
            
    return {"index": best_idx, "point": best_pt, "distance_km": best_dist}

def sort_by_distance(target_lat: float, target_lon: float, locations: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    """Sort list of locations by proximity to P."""
    ranked = []
    for idx, (lat, lon) in enumerate(locations):
        d = distance_ops.calculate_geodesic(target_lat, target_lon, lat, lon)
        ranked.append({"index": idx, "point": (lat, lon), "distance_km": d})
    
    return sorted(ranked, key=lambda x: x["distance_km"])

def bulk_get_countries(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[str]:
    """Get list of countries for list of coords."""
    results = []
    for lat, lon in coords:
        try:
            c = geocode_ops.get_country(lat, lon)
            results.append(c)
        except:
            results.append("Error")
        time.sleep(delay)
    return results

def validate_addresses_bulk(addresses: List[str], delay: float = 1.0) -> Dict[str, bool]:
    """Check if addresses resolve."""
    results = {}
    for addr in addresses:
        try:
            res = geocode_ops.geocode_address(addr)
            results[addr] = "latitude" in res
        except:
            results[addr] = False
        time.sleep(delay)
    return results
