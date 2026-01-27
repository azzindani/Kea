from mcp_servers.duckdb_server.tools import core_ops
from typing import Dict, Any, List

def _ensure_spatial():
    """Ensure spatial extension is loaded."""
    con = core_ops.get_connection()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
    except:
        pass # Might already be loaded or fail if no internet/permission

def st_point(lat: float, lon: float) -> str:
    """Create point geometry WKT."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        # returns geometry object usually, let's return WKT text
        res = con.execute(f"SELECT ST_AsText(ST_Point({lon}, {lat}))").fetchone()
        return res[0]
    except Exception as e:
        return f"Error: {e}"

def st_distance(wkt_a: str, wkt_b: str) -> float:
    """Calculate distance between geometries."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        # ST_Distance
        res = con.execute(f"SELECT ST_Distance(ST_GeomFromText('{wkt_a}'), ST_GeomFromText('{wkt_b}'))").fetchone()
        return res[0]
    except Exception as e:
        return -1.0

def st_area(wkt_poly: str) -> float:
    """Calculate area of polygon."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_Area(ST_GeomFromText('{wkt_poly}'))").fetchone()
        return res[0]
    except Exception as e:
        return -1.0

def st_contains(wkt_a: str, wkt_b: str) -> bool:
    """Check if geom A contains geom B."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_Contains(ST_GeomFromText('{wkt_a}'), ST_GeomFromText('{wkt_b}'))").fetchone()
        return bool(res[0])
    except Exception as e:
        return False

def st_intersects(wkt_a: str, wkt_b: str) -> bool:
    """Check intersection."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_Intersects(ST_GeomFromText('{wkt_a}'), ST_GeomFromText('{wkt_b}'))").fetchone()
        return bool(res[0])
    except Exception as e:
        return False

def st_buffer(wkt_geom: str, dist: float) -> str:
    """Create buffer around geometry."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_AsText(ST_Buffer(ST_GeomFromText('{wkt_geom}'), {dist}))").fetchone()
        return res[0]
    except Exception as e:
        return f"Error: {e}"

def st_centroid(wkt_geom: str) -> str:
    """Get center of geometry."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_AsText(ST_Centroid(ST_GeomFromText('{wkt_geom}'))").fetchone()
        return res[0]
    except Exception as e:
        return f"Error: {e}"

def st_read(file_path: str, table_name: str) -> str:
    """Load spatial file (GeoJSON/Shapefile) via driver."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        # ST_Read handles various formats
        query = f"CREATE TABLE {table_name} AS SELECT * FROM ST_Read('{file_path}')"
        con.execute(query)
        return f"Loaded spatial data from {file_path} into {table_name}"
    except Exception as e:
        return f"Error: {e}"

def st_as_text(wkb_col: str, table_name: str) -> List[str]:
    """Convert WKB column to WKT text (preview)."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        res = con.execute(f"SELECT ST_AsText({wkb_col}) FROM {table_name} LIMIT 20").fetchall()
        return [r[0] for r in res]
    except Exception as e:
        return [f"Error: {e}"]

def st_as_geojson(wkt_geom: str) -> str:
    """Convert WKT to GeoJSON."""
    _ensure_spatial()
    con = core_ops.get_connection()
    try:
        # Only some versions support ST_AsGeoJSON, fallback to text if not
        res = con.execute(f"SELECT ST_AsGeoJSON(ST_GeomFromText('{wkt_geom}'))").fetchone()
        return res[0]
    except Exception as e:
        return f"Error: {e}"
