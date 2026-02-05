from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
from typing import Dict, Any, List, Optional, Union

async def plot_scatter_map(data: DataInput, lat: str, lon: str, color: Optional[str] = None, size: Optional[str] = None, hover_name: Optional[str] = None, zoom: int = 3, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a scatter map (using MapLibre/OSM)."""
    df = parse_data_frame(data)
    # Use scatter_mapbox or scatter_geo depending on preference?
    # px.scatter_map is newer but might require token for some styles
    # px.scatter_geo is simpler for global
    # Let's use scatter_geo for simplicity/independence
    fig = px.scatter_geo(df, lat=lat, lon=lon, color=color, size=size, hover_name=hover_name, title=title)
    fig.update_geos(projection_type="natural earth")
    return get_figure_output(fig, format=format)

async def plot_choropleth(data: DataInput, locations: str, color: str, locationmode: str = 'ISO-3', hover_name: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a choropleth map."""
    df = parse_data_frame(data)
    fig = px.choropleth(df, locations=locations, color=color, locationmode=locationmode, hover_name=hover_name, title=title)
    return get_figure_output(fig, format=format)

async def plot_density_map(data: DataInput, lat: str, lon: str, z: Optional[str] = None, radius: int = 10, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a density heatmap on a map."""
    df = parse_data_frame(data)
    fig = px.density_mapbox(df, lat=lat, lon=lon, z=z, radius=radius, title=title, mapbox_style="stamen-terrain")
    # Note: mapbox_style might default to something requiring token. 'open-street-map' is free.
    fig.update_layout(mapbox_style="open-street-map") 
    return get_figure_output(fig, format=format)
