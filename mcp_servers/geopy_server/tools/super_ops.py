from typing import List, Dict, Any, Tuple
from mcp_servers.geopy_server.tools import geocode_ops, distance_ops, bulk_ops
import pandas as pd
import io

def solve_tsp(locations: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Traveling Salesman (Simple Nearest Neighbor heuristic)."""
    # Start at 0
    if not locations: return {"path": [], "distance": 0}
    
    unvisited = set(range(1, len(locations)))
    current = 0
    path = [0]
    total_dist = 0.0
    
    while unvisited:
        nearest = None
        min_dist = float('inf')
        
        for idx in unvisited:
            d = distance_ops.calculate_geodesic(locations[current][0], locations[current][1], locations[idx][0], locations[idx][1])
            if d < min_dist:
                min_dist = d
                nearest = idx
        
        current = nearest
        unvisited.remove(current)
        path.append(current)
        total_dist += min_dist
        
    # Return to start? Usually TSP does.
    last = path[-1]
    first = path[0]
    d_return = distance_ops.calculate_geodesic(locations[last][0], locations[last][1], locations[first][0], locations[first][1])
    total_dist += d_return
    path.append(first)
    
    return {
        "ordered_indices": path,
        "total_distance_km": total_dist,
        "ordered_points": [locations[i] for i in path]
    }

def cluster_points(locations: List[Tuple[float, float]], threshold_km: float) -> List[List[Tuple[float, float]]]:
    """Simple clustering (group points within threshold of leader)."""
    clusters = []
    # Very naive: Greedy clustering
    pool = set(range(len(locations)))
    
    while pool:
        leader_idx = pool.pop()
        leader = locations[leader_idx]
        cluster = [leader]
        
        to_remove = []
        for other_idx in pool:
            other = locations[other_idx]
            d = distance_ops.calculate_geodesic(leader[0], leader[1], other[0], other[1])
            if d <= threshold_km:
                cluster.append(other)
                to_remove.append(other_idx)
                
        for i in to_remove:
             pool.remove(i)
        
        clusters.append(cluster)
    return clusters

def get_bounding_box(locations: List[Tuple[float, float]]) -> Dict[str, float]:
    """Lat/Lon min/max for list of points."""
    if not locations: return {}
    lats = [p[0] for p in locations]
    lons = [p[1] for p in locations]
    return {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons)
    }

def find_points_in_radius(center_lat: float, center_lon: float, locations: List[Tuple[float, float]], radius_km: float) -> List[Tuple[float, float]]:
    """Filter list of points within R km of Center."""
    res = []
    for lat, lon in locations:
        if distance_ops.is_within_distance(center_lat, center_lon, lat, lon, radius_km):
            res.append((lat, lon))
    return res

def generate_grid_in_box(min_lat: float, min_lon: float, max_lat: float, max_lon: float, step_km: float) -> List[Tuple[float, float]]:
    """Create grid of points within bounding box."""
    # Rough approximation: 1 degree lat ~ 111km. 
    lat_step = step_km / 111.0
    # Longitude step varies by latitude: 111 * cos(lat)
    import math
    avg_lat = (min_lat + max_lat) / 2
    lon_scale = 111.0 * math.cos(math.radians(avg_lat))
    lon_step = step_km / max(lon_scale, 0.1)
    
    points = []
    curr_lat = min_lat
    while curr_lat <= max_lat:
        curr_lon = min_lon
        while curr_lon <= max_lon:
            points.append((curr_lat, curr_lon))
            curr_lon += lon_step
        curr_lat += lat_step
    return points

def calculate_total_route_distance(locations: List[Tuple[float, float]]) -> float:
    """Sum of distances for ordered path (A->B->C...)."""
    dist = 0.0
    for i in range(len(locations)-1):
        dist += distance_ops.calculate_geodesic(locations[i][0], locations[i][1], locations[i+1][0], locations[i+1][1])
    return dist

def find_centroid(locations: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Geographic center of mass."""
    # Simple average
    if not locations: return (0.0, 0.0)
    avg_lat = sum(p[0] for p in locations) / len(locations)
    avg_lon = sum(p[1] for p in locations) / len(locations)
    return (avg_lat, avg_lon)

def geocode_dataframe_csv(input_csv: str, address_col: str, output_csv: str) -> str:
    """Read CSV, geocode column, save CSV."""
    try:
        df = pd.read_csv(input_csv)
        if address_col not in df.columns: return f"Error: {address_col} not in CSV"
        
        # Limit rows to avoid ban? 
        # For now proceed with 1s delay
        
        lats = []
        lons = []
        
        for addr in df[address_col]:
            try:
                # Cache checking logic omitted for brevity
                res = geocode_ops.geocode_address(str(addr))
                lats.append(res.get("latitude"))
                lons.append(res.get("longitude"))
            except:
                lats.append(None)
                lons.append(None)
            time.sleep(1.0)
            
        df["latitude"] = lats
        df["longitude"] = lons
        df.to_csv(output_csv, index=False)
        return f"Geocoded CSV saved to {output_csv}"
    except Exception as e:
        return f"Error: {e}"

def reverse_geocode_dataframe_csv(input_csv: str, lat_col: str, lon_col: str, output_csv: str) -> str:
    """Read CSV with lat/lon, add address."""
    try:
        df = pd.read_csv(input_csv)
        addrs = []
        for idx, row in df.iterrows():
            try:
                res = geocode_ops.reverse_geocode(row[lat_col], row[lon_col])
                addrs.append(res.get("address"))
            except:
                addrs.append(None)
            time.sleep(1.0)
        df["address"] = addrs
        df.to_csv(output_csv, index=False)
        return f"Reverse geocoded CSV to {output_csv}"
    except Exception as e:
        return f"Error: {e}"

def group_by_proximity(locations: List[Tuple[float, float]], threshold_km: float) -> Dict[int, List[Tuple[float, float]]]:
    """Alias/Wrapper for clustering."""
    clusters = cluster_points(locations, threshold_km)
    return {i: c for i, c in enumerate(clusters)}

def find_outliers(locations: List[Tuple[float, float]], threshold_km: float) -> List[Tuple[float, float]]:
    """ID points far from the centroid."""
    centroid = find_centroid(locations)
    outliers = []
    for p in locations:
        d = distance_ops.calculate_geodesic(centroid[0], centroid[1], p[0], p[1])
        if d > threshold_km:
            outliers.append(p)
    return outliers

def parse_location_name(full_address: str) -> Dict[str, str]:
    """Extract structured parts (naive parse, better done via raw info)."""
    # This is speculative, better to rely on get_city/country tools
    return {"message": "Use get_city/get_country for structured extraction from coordinates."}

def detect_region_type(locations: List[Tuple[float, float]]) -> str:
    """Guess if urban/rural based on density."""
    # Bounding box area / count
    box = get_bounding_box(locations)
    if not box: return "Unknown"
    
    # Approx area
    lat_dist = distance_ops.calculate_geodesic(box["min_lat"], box["min_lon"], box["max_lat"], box["min_lon"])
    lon_dist = distance_ops.calculate_geodesic(box["min_lat"], box["min_lon"], box["min_lat"], box["max_lon"])
    area = lat_dist * lon_dist
    
    if area == 0: return "Single Point"
    density = len(locations) / area # points per sq km
    
    if density > 1000: return "Urban High Density"
    if density > 100: return "Suburban"
    return "Rural/Sparse"

def calculate_area_polygon(locations: List[Tuple[float, float]]) -> float:
    """Area of polygon (Shoelace formula approx or library)."""
    # Requires projection to plane for simple calc, or spherical area formula
    # Placeholder
    return -1.0

def calculate_perimeter_polygon(locations: List[Tuple[float, float]]) -> float:
    """Perimeter of connected points."""
    # Closes the loop
    if not locations: return 0.0
    perim = calculate_total_route_distance(locations)
    # Plus close
    perim += distance_ops.calculate_geodesic(locations[-1][0], locations[-1][1], locations[0][0], locations[0][1])
    return perim

def simplify_path(locations: List[Tuple[float, float]], tolerance_km: float) -> List[Tuple[float, float]]:
    """Douglas-Peucker reduction placeholder."""
    return locations

def interpolate_points(lat1: float, lon1: float, lat2: float, lon2: float, num_points: int) -> List[Tuple[float, float]]:
    """Generate points along line A-B."""
    pts = []
    for i in range(num_points + 1):
        frac = i / num_points
        lat = lat1 + (lat2 - lat1) * frac
        lon = lon1 + (lon2 - lon1) * frac
        pts.append((lat, lon))
    return pts

def bearing_at_waypoints(locations: List[Tuple[float, float]]) -> List[float]:
    """Calculate bearings for a route segments."""
    bearings = []
    for i in range(len(locations)-1):
        b = distance_ops.calculate_bearing(locations[i][0], locations[i][1], locations[i+1][0], locations[i+1][1])
        bearings.append(b)
    return bearings

def export_to_kml(locations: List[Tuple[float, float]], output_file: str) -> str:
    """Create KML file."""
    # Simple KML xml construction
    kml = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2">', '<Document>']
    for lat, lon in locations:
        kml.append(f'<Placemark><Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>')
    kml.append('</Document></kml>')
    
    try:
        with open(output_file, 'w') as f:
            f.write('\n'.join(kml))
        return f"KML saved to {output_file}"
    except Exception as e:
        return f"Error: {e}"
