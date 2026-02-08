
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "geopy",
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.geopy_server.tools import (
    core_ops, geocode_ops, distance_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("geopy_server", dependencies=["pandas", "geopy"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def get_version() -> str: 
    """FETCHES version. [ACTION]
    
    [RAG Context]
    Get installed Geopy version.
    Returns version string.
    """
    return core_ops.get_version()

@mcp.tool()
def set_user_agent(ua: str) -> str: 
    """SETS user agent. [ACTION]
    
    [RAG Context]
    Set custom User-Agent for requests.
    Returns status string.
    """
    return core_ops.set_user_agent(ua)

@mcp.tool()
def set_geocoder_service(service: str) -> str: 
    """SETS service. [ACTION]
    
    [RAG Context]
    Select geocoding service (Nominatim, Google, etc).
    Returns status string.
    """
    return core_ops.set_geocoder_service(service)

@mcp.tool()
def set_api_key(key: str) -> str: 
    """SETS key. [ACTION]
    
    [RAG Context]
    Set API key for paid services.
    Returns status string.
    """
    return core_ops.set_api_key(key)

@mcp.tool()
def set_timeout(seconds: int) -> str: 
    """SETS timeout. [ACTION]
    
    [RAG Context]
    Set request timeout in seconds.
    Returns status string.
    """
    return core_ops.set_timeout(seconds)

# ==========================================
# 2. Geocoding
# ==========================================
@mcp.tool()
def geocode_address(query: str) -> Dict[str, Any]: 
    """GEOCODES address. [ACTION]
    
    [RAG Context]
    Convert address to coordinates.
    Returns JSON dict.
    """
    return geocode_ops.geocode_address(query)

@mcp.tool()
def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]: 
    """REVERSES geocode. [ACTION]
    
    [RAG Context]
    Convert coordinates to address.
    Returns JSON dict.
    """
    return geocode_ops.reverse_geocode(lat, lon)

@mcp.tool()
def get_coordinates(query: str) -> Tuple[float, float]: 
    """FETCHES coords. [ACTION]
    
    [RAG Context]
    Get lat/lon tuple for address.
    Returns float tuple.
    """
    return geocode_ops.get_coordinates(query)

@mcp.tool()
def get_full_address(lat: float, lon: float) -> str: 
    """FETCHES address. [ACTION]
    
    [RAG Context]
    Get formatted address from coordinates.
    Returns string.
    """
    return geocode_ops.get_full_address(lat, lon)

@mcp.tool()
def get_altitude(query: str) -> float: 
    """FETCHES altitude. [ACTION]
    
    [RAG Context]
    Get altitude for location (if available).
    Returns float meters.
    """
    return geocode_ops.get_altitude(query)

@mcp.tool()
def get_zipcode(lat: float, lon: float) -> str: 
    """FETCHES zipcode. [ACTION]
    
    [RAG Context]
    Extract postal code from location.
    Returns string.
    """
    return geocode_ops.get_zipcode(lat, lon)

@mcp.tool()
def get_country(lat: float, lon: float) -> str: 
    """FETCHES country. [ACTION]
    
    [RAG Context]
    Extract country name from location.
    Returns string.
    """
    return geocode_ops.get_country(lat, lon)

@mcp.tool()
def get_city(lat: float, lon: float) -> str: 
    """FETCHES city. [ACTION]
    
    [RAG Context]
    Extract city/town name from location.
    Returns string.
    """
    return geocode_ops.get_city(lat, lon)

@mcp.tool()
def get_raw_info(query: str) -> Dict[str, Any]: 
    """FETCHES raw info. [ACTION]
    
    [RAG Context]
    Get full raw response from geocoder.
    Returns JSON dict.
    """
    return geocode_ops.get_raw_info(query)

@mcp.tool()
def geocode_with_box(query: str, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> Dict[str, Any]: 
    """GEOCODES bounded. [ACTION]
    
    [RAG Context]
    Geocode within a bounding box.
    Returns JSON dict.
    """
    return geocode_ops.geocode_with_box(query, min_lat, min_lon, max_lat, max_lon)

@mcp.tool()
def geocode_structured(street: str = "", city: str = "", country: str = "") -> Dict[str, Any]: 
    """GEOCODES structured. [ACTION]
    
    [RAG Context]
    Geocode using structured components.
    Returns JSON dict.
    """
    return geocode_ops.geocode_structured(street, city, country)

# ==========================================
# 3. Distance
# ==========================================
@mcp.tool()
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float: 
    """CALCULATES distance. [ACTION]
    
    [RAG Context]
    Calculate great-circle distance (km).
    Returns float km.
    """
    return distance_ops.calculate_distance(lat1, lon1, lat2, lon2)

@mcp.tool()
def calculate_geodesic(lat1: float, lon1: float, lat2: float, lon2: float) -> float: 
    """CALCULATES geodesic. [ACTION]
    
    [RAG Context]
    Calculate precise geodesic distance (Vincenty).
    Returns float km.
    """
    return distance_ops.calculate_geodesic(lat1, lon1, lat2, lon2)

@mcp.tool()
def get_destination_point(lat: float, lon: float, bearing: float, dist_km: float) -> Tuple[float, float]: 
    """CALCULATES destination. [ACTION]
    
    [RAG Context]
    Find coordinates given start, bearing, distance.
    Returns float tuple.
    """
    return distance_ops.get_destination_point(lat, lon, bearing, dist_km)

@mcp.tool()
def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float: 
    """CALCULATES bearing. [ACTION]
    
    [RAG Context]
    Calculate initial bearing between points.
    Returns float degrees.
    """
    return distance_ops.calculate_bearing(lat1, lon1, lat2, lon2)

@mcp.tool()
def is_within_distance(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool: 
    """CHECKS proximity. [ACTION]
    
    [RAG Context]
    Check if two points are within radius.
    Returns boolean.
    """
    return distance_ops.is_within_distance(lat1, lon1, lat2, lon2, radius_km)

@mcp.tool()
def convert_units(km: float, unit: str = "miles") -> float: 
    """CONVERTS units. [ACTION]
    
    [RAG Context]
    Convert km to miles, feet, meters.
    Returns float.
    """
    return distance_ops.convert_units(km, unit)

@mcp.tool()
def get_middle_point(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]: 
    """CALCULATES midpoint. [ACTION]
    
    [RAG Context]
    Find midpoint between two coordinates.
    Returns float tuple.
    """
    return distance_ops.get_middle_point(lat1, lon1, lat2, lon2)

# ==========================================
# 4. Bulk
# ==========================================
# ==========================================
# 4. Bulk
# ==========================================
@mcp.tool()
def bulk_geocode(queries: List[str], delay: float = 1.0) -> List[Dict[str, Any]]: 
    """BULK: Geocode. [ACTION]
    
    [RAG Context]
    Geocode multiple addresses with rate limiting.
    Returns list of dicts.
    """
    return bulk_ops.bulk_geocode(queries, delay)

@mcp.tool()
def bulk_reverse(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[Dict[str, Any]]: 
    """BULK: Reverse. [ACTION]
    
    [RAG Context]
    Reverse geocode multiple coordinates.
    Returns list of dicts.
    """
    return bulk_ops.bulk_reverse(coords, delay)

@mcp.tool()
def calculate_distance_matrix(locations: List[Tuple[float, float]]) -> List[List[float]]: 
    """CALCULATES matrix. [ACTION]
    
    [RAG Context]
    Compute distance matrix for all point pairs.
    Returns 2D list of floats.
    """
    return bulk_ops.calculate_distance_matrix(locations)

@mcp.tool()
def find_nearest(target_lat: float, target_lon: float, candidates: List[Tuple[float, float]]) -> Dict[str, Any]: 
    """FINDS nearest. [ACTION]
    
    [RAG Context]
    Find closest point from candidates.
    Returns dict with point and distance.
    """
    return bulk_ops.find_nearest(target_lat, target_lon, candidates)

@mcp.tool()
def sort_by_distance(target_lat: float, target_lon: float, locations: List[Tuple[float, float]]) -> List[Dict[str, Any]]: 
    """SORTS locations. [ACTION]
    
    [RAG Context]
    Sort locations by distance from target.
    Returns list of sorted dicts.
    """
    return bulk_ops.sort_by_distance(target_lat, target_lon, locations)

@mcp.tool()
def bulk_get_countries(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[str]: 
    """BULK: Countries. [ACTION]
    
    [RAG Context]
    Get country for multiple coordinates.
    Returns list of strings.
    """
    return bulk_ops.bulk_get_countries(coords, delay)

@mcp.tool()
def validate_addresses_bulk(addresses: List[str], delay: float = 1.0) -> Dict[str, bool]: 
    """VALIDATES bulk. [ACTION]
    
    [RAG Context]
    Check if multiple addresses exist.
    Returns dict of address->bool.
    """
    return bulk_ops.validate_addresses_bulk(addresses, delay)

# ==========================================
# 5. Super Tools
# ==========================================
@mcp.tool()
def solve_tsp(locations: List[Tuple[float, float]]) -> Dict[str, Any]: 
    """SOLVES TSP. [ACTION]
    
    [RAG Context]
    Solve Traveling Salesperson Problem (nearest neighbor).
    Returns dict with route and distance.
    """
    return super_ops.solve_tsp(locations)

@mcp.tool()
def cluster_points(locations: List[Tuple[float, float]], threshold_km: float) -> List[List[Tuple[float, float]]]: 
    """CLUSTERS points. [ACTION]
    
    [RAG Context]
    Group points within distance threshold.
    Returns list of clusters.
    """
    return super_ops.cluster_points(locations, threshold_km)

@mcp.tool()
def get_bounding_box(locations: List[Tuple[float, float]]) -> Dict[str, float]: 
    """CALCULATES bounds. [ACTION]
    
    [RAG Context]
    Get min/max lat/lon for points.
    Returns dict bounds.
    """
    return super_ops.get_bounding_box(locations)

@mcp.tool()
def find_points_in_radius(center_lat: float, center_lon: float, locations: List[Tuple[float, float]], radius_km: float) -> List[Tuple[float, float]]: 
    """FILTERS radius. [ACTION]
    
    [RAG Context]
    Find all points within radius of center.
    Returns list of tuples.
    """
    return super_ops.find_points_in_radius(center_lat, center_lon, locations, radius_km)

@mcp.tool()
def generate_grid_in_box(min_lat: float, min_lon: float, max_lat: float, max_lon: float, step_km: float) -> List[Tuple[float, float]]: 
    """GENERATES grid. [ACTION]
    
    [RAG Context]
    Create grid of points within bounding box.
    Returns list of tuples.
    """
    return super_ops.generate_grid_in_box(min_lat, min_lon, max_lat, max_lon, step_km)

@mcp.tool()
def calculate_total_route_distance(locations: List[Tuple[float, float]]) -> float: 
    """CALCULATES route. [ACTION]
    
    [RAG Context]
    Calculate total distance of ordered path.
    Returns float km.
    """
    return super_ops.calculate_total_route_distance(locations)

@mcp.tool()
def find_centroid(locations: List[Tuple[float, float]]) -> Tuple[float, float]: 
    """CALCULATES centroid. [ACTION]
    
    [RAG Context]
    Find geometric center of points.
    Returns float tuple.
    """
    return super_ops.find_centroid(locations)

@mcp.tool()
def geocode_dataframe_csv(input_csv: str, address_col: str, output_csv: str) -> str: 
    """GEOCODES CSV. [ACTION]
    
    [RAG Context]
    Geocode address column in CSV file.
    Returns output path.
    """
    return super_ops.geocode_dataframe_csv(input_csv, address_col, output_csv)

@mcp.tool()
def reverse_geocode_dataframe_csv(input_csv: str, lat_col: str, lon_col: str, output_csv: str) -> str: 
    """REVERSES CSV. [ACTION]
    
    [RAG Context]
    Reverse geocode lat/lon cols in CSV.
    Returns output path.
    """
    return super_ops.reverse_geocode_dataframe_csv(input_csv, lat_col, lon_col, output_csv)

@mcp.tool()
def group_by_proximity(locations: List[Tuple[float, float]], threshold_km: float) -> Dict[int, List[Tuple[float, float]]]: 
    """GROUPS points. [ACTION]
    
    [RAG Context]
    Group points by spatial proximity.
    Returns dict of groups.
    """
    return super_ops.group_by_proximity(locations, threshold_km)

@mcp.tool()
def find_outliers(locations: List[Tuple[float, float]], threshold_km: float) -> List[Tuple[float, float]]: 
    """FINDS outliers. [ACTION]
    
    [RAG Context]
    Find points far from all others.
    Returns list of tuples.
    """
    return super_ops.find_outliers(locations, threshold_km)

@mcp.tool()
def detect_region_type(locations: List[Tuple[float, float]]) -> str: 
    """DETECTS region. [ACTION]
    
    [RAG Context]
    Guess region type (urban/rural) from density.
    Returns classification string.
    """
    return super_ops.detect_region_type(locations)

@mcp.tool()
def calculate_perimeter_polygon(locations: List[Tuple[float, float]]) -> float: 
    """CALCULATES perimeter. [ACTION]
    
    [RAG Context]
    Calculate perimeter of polygon from points.
    Returns float km.
    """
    return super_ops.calculate_perimeter_polygon(locations)

@mcp.tool()
def interpolate_points(lat1: float, lon1: float, lat2: float, lon2: float, num_points: int) -> List[Tuple[float, float]]: 
    """INTERPOLATES path. [ACTION]
    
    [RAG Context]
    Generate points along line between A and B.
    Returns list of tuples.
    """
    return super_ops.interpolate_points(lat1, lon1, lat2, lon2, num_points)

@mcp.tool()
def bearing_at_waypoints(locations: List[Tuple[float, float]]) -> List[float]: 
    """CALCULATES bearings. [ACTION]
    
    [RAG Context]
    Calculate bearing at each point in path.
    Returns list of degrees.
    """
    return super_ops.bearing_at_waypoints(locations)

@mcp.tool()
def export_to_kml(locations: List[Tuple[float, float]], output_file: str) -> str: 
    """EXPORTS KML. [ACTION]
    
    [RAG Context]
    Save points to KML file for Google Earth.
    Returns output path.
    """
    return super_ops.export_to_kml(locations, output_file)

if __name__ == "__main__":
    mcp.run()