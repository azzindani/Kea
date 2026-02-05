from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput, VectorInput
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union

async def plot_candlestick(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a candlestick chart."""
    df = parse_data_frame(data)
    fig = go.Figure(data=[go.Candlestick(
        x=df[x], open=df[open], high=df[high], low=df[low], close=df[close]
    )])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_ohlc(data: DataInput, x: str, open: str, high: str, low: str, close: str, title: Optional[str] = None, format: str = 'png') -> str:
    """Create an OHLC chart."""
    df = parse_data_frame(data)
    fig = go.Figure(data=[go.Ohlc(
        x=df[x], open=df[open], high=df[high], low=df[low], close=df[close]
    )])
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_waterfall(data: DataInput, x: str, y: str, measure: Optional[str] = None, text: Optional[str] = None, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a waterfall chart. measure: list of 'relative', 'total', etc."""
    df = parse_data_frame(data)
    
    measure_vec = df[measure] if measure else None
    text_vec = df[text] if text else None
    
    fig = go.Figure(go.Waterfall(
        x=df[x], y=df[y], measure=measure_vec, text=text_vec
    ))
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_funnel(data: DataInput, x: str, y: str, title: Optional[str] = None, format: str = 'png') -> str:
    """Create a funnel chart."""
    df = parse_data_frame(data)
    fig = go.Figure(go.Funnel(
        y=df[y], x=df[x]
    ))
    if title: fig.update_layout(title=title)
    return get_figure_output(fig, format=format)

async def plot_indicator(value: float, delta_ref: Optional[float] = None, title: Optional[str] = None, mode: str = "number+delta", format: str = 'png') -> str:
    """Create an indicator (gauge/big number)."""
    fig = go.Figure(go.Indicator(
        mode=mode,
        value=value,
        delta={'reference': delta_ref} if delta_ref is not None else None,
        title={'text': title} if title else None
    ))
    return get_figure_output(fig, format=format)
