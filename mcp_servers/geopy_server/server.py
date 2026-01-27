from mcp.server.fastmcp import FastMCP
from mcp_servers.geopy_server.tools import (
    core_ops, geocode_ops, distance_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("geopy_server", dependencies=["pandas", "geopy"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def get_version() -> str: return core_ops.get_version()
@mcp.tool()
def set_user_agent(ua: str) -> str: return core_ops.set_user_agent(ua)
@mcp.tool()
def set_geocoder_service(service: str) -> str: return core_ops.set_geocoder_service(service)
@mcp.tool()
def set_api_key(key: str) -> str: return core_ops.set_api_key(key)
@mcp.tool()
def set_timeout(seconds: int) -> str: return core_ops.set_timeout(seconds)

# ==========================================
# 2. Geocoding
# ==========================================
@mcp.tool()
def geocode_address(query: str) -> Dict[str, Any]: return geocode_ops.geocode_address(query)
@mcp.tool()
def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]: return geocode_ops.reverse_geocode(lat, lon)
@mcp.tool()
def get_coordinates(query: str) -> Tuple[float, float]: return geocode_ops.get_coordinates(query)
@mcp.tool()
def get_full_address(lat: float, lon: float) -> str: return geocode_ops.get_full_address(lat, lon)
@mcp.tool()
def get_altitude(query: str) -> float: return geocode_ops.get_altitude(query)
@mcp.tool()
def get_zipcode(lat: float, lon: float) -> str: return geocode_ops.get_zipcode(lat, lon)
@mcp.tool()
def get_country(lat: float, lon: float) -> str: return geocode_ops.get_country(lat, lon)
@mcp.tool()
def get_city(lat: float, lon: float) -> str: return geocode_ops.get_city(lat, lon)
@mcp.tool()
def get_raw_info(query: str) -> Dict[str, Any]: return geocode_ops.get_raw_info(query)
@mcp.tool()
def geocode_with_box(query: str, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> Dict[str, Any]: return geocode_ops.geocode_with_box(query, min_lat, min_lon, max_lat, max_lon)
@mcp.tool()
def geocode_structured(street: str = "", city: str = "", country: str = "") -> Dict[str, Any]: return geocode_ops.geocode_structured(street, city, country)

# ==========================================
# 3. Distance
# ==========================================
@mcp.tool()
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float: return distance_ops.calculate_distance(lat1, lon1, lat2, lon2)
@mcp.tool()
def calculate_geodesic(lat1: float, lon1: float, lat2: float, lon2: float) -> float: return distance_ops.calculate_geodesic(lat1, lon1, lat2, lon2)
@mcp.tool()
def get_destination_point(lat: float, lon: float, bearing: float, dist_km: float) -> Tuple[float, float]: return distance_ops.get_destination_point(lat, lon, bearing, dist_km)
@mcp.tool()
def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float: return distance_ops.calculate_bearing(lat1, lon1, lat2, lon2)
@mcp.tool()
def is_within_distance(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool: return distance_ops.is_within_distance(lat1, lon1, lat2, lon2, radius_km)
@mcp.tool()
def convert_units(km: float, unit: str = "miles") -> float: return distance_ops.convert_units(km, unit)
@mcp.tool()
def get_middle_point(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]: return distance_ops.get_middle_point(lat1, lon1, lat2, lon2)

# ==========================================
# 4. Bulk
# ==========================================
@mcp.tool()
def bulk_geocode(queries: List[str], delay: float = 1.0) -> List[Dict[str, Any]]: return bulk_ops.bulk_geocode(queries, delay)
@mcp.tool()
def bulk_reverse(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[Dict[str, Any]]: return bulk_ops.bulk_reverse(coords, delay)
@mcp.tool()
def calculate_distance_matrix(locations: List[Tuple[float, float]]) -> List[List[float]]: return bulk_ops.calculate_distance_matrix(locations)
@mcp.tool()
def find_nearest(target_lat: float, target_lon: float, candidates: List[Tuple[float, float]]) -> Dict[str, Any]: return bulk_ops.find_nearest(target_lat, target_lon, candidates)
@mcp.tool()
def sort_by_distance(target_lat: float, target_lon: float, locations: List[Tuple[float, float]]) -> List[Dict[str, Any]]: return bulk_ops.sort_by_distance(target_lat, target_lon, locations)
@mcp.tool()
def bulk_get_countries(coords: List[Tuple[float, float]], delay: float = 1.0) -> List[str]: return bulk_ops.bulk_get_countries(coords, delay)
@mcp.tool()
def validate_addresses_bulk(addresses: List[str], delay: float = 1.0) -> Dict[str, bool]: return bulk_ops.validate_addresses_bulk(addresses, delay)

# ==========================================
# 5. Super Tools
# ==========================================
@mcp.tool()
def solve_tsp(locations: List[Tuple[float, float]]) -> Dict[str, Any]: return super_ops.solve_tsp(locations)
@mcp.tool()
def cluster_points(locations: List[Tuple[float, float]], threshold_km: float) -> List[List[Tuple[float, float]]]: return super_ops.cluster_points(locations, threshold_km)
@mcp.tool()
def get_bounding_box(locations: List[Tuple[float, float]]) -> Dict[str, float]: return super_ops.get_bounding_box(locations)
@mcp.tool()
def find_points_in_radius(center_lat: float, center_lon: float, locations: List[Tuple[float, float]], radius_km: float) -> List[Tuple[float, float]]: return super_ops.find_points_in_radius(center_lat, center_lon, locations, radius_km)
@mcp.tool()
def generate_grid_in_box(min_lat: float, min_lon: float, max_lat: float, max_lon: float, step_km: float) -> List[Tuple[float, float]]: return super_ops.generate_grid_in_box(min_lat, min_lon, max_lat, max_lon, step_km)
@mcp.tool()
def calculate_total_route_distance(locations: List[Tuple[float, float]]) -> float: return super_ops.calculate_total_route_distance(locations)
@mcp.tool()
def find_centroid(locations: List[Tuple[float, float]]) -> Tuple[float, float]: return super_ops.find_centroid(locations)
@mcp.tool()
def geocode_dataframe_csv(input_csv: str, address_col: str, output_csv: str) -> str: return super_ops.geocode_dataframe_csv(input_csv, address_col, output_csv)
@mcp.tool()
def reverse_geocode_dataframe_csv(input_csv: str, lat_col: str, lon_col: str, output_csv: str) -> str: return super_ops.reverse_geocode_dataframe_csv(input_csv, lat_col, lon_col, output_csv)
@mcp.tool()
def group_by_proximity(locations: List[Tuple[float, float]], threshold_km: float) -> Dict[int, List[Tuple[float, float]]]: return super_ops.group_by_proximity(locations, threshold_km)
@mcp.tool()
def find_outliers(locations: List[Tuple[float, float]], threshold_km: float) -> List[Tuple[float, float]]: return super_ops.find_outliers(locations, threshold_km)
@mcp.tool()
def detect_region_type(locations: List[Tuple[float, float]]) -> str: return super_ops.detect_region_type(locations)
@mcp.tool()
def calculate_perimeter_polygon(locations: List[Tuple[float, float]]) -> float: return super_ops.calculate_perimeter_polygon(locations)
@mcp.tool()
def interpolate_points(lat1: float, lon1: float, lat2: float, lon2: float, num_points: int) -> List[Tuple[float, float]]: return super_ops.interpolate_points(lat1, lon1, lat2, lon2, num_points)
@mcp.tool()
def bearing_at_waypoints(locations: List[Tuple[float, float]]) -> List[float]: return super_ops.bearing_at_waypoints(locations)
@mcp.tool()
def export_to_kml(locations: List[Tuple[float, float]], output_file: str) -> str: return super_ops.export_to_kml(locations, output_file)

if __name__ == "__main__":
    mcp.run()
