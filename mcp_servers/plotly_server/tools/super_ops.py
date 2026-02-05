from mcp_servers.plotly_server.tools.core_ops import parse_data_frame, get_figure_output, DataInput
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List, Optional, Union

async def auto_plot(data: DataInput, x: str, y: Optional[str] = None, color: Optional[str] = None, format: str = 'png') -> str:
    """
    Intelligently select and draw a plot based on variable types.
    """
    df = parse_data_frame(data)
    is_x_num = pd.api.types.is_numeric_dtype(df[x])
    is_y_num = pd.api.types.is_numeric_dtype(df[y]) if y else False
    
    if y is None:
        if is_x_num:
            fig = px.histogram(df, x=x, color=color, marginal='box')
        else:
            fig = px.pie(df, names=x, title=f"Distribution of {x}")
    else:
        if is_x_num and is_y_num:
            fig = px.scatter(df, x=x, y=y, color=color, trendline='ols')
        elif not is_x_num and is_y_num:
            fig = px.box(df, x=x, y=y, color=color)
        elif is_x_num and not is_y_num:
            fig = px.box(df, x=y, y=x, color=color, orientation='h')
        else:
            fig = px.density_heatmap(df, x=x, y=y)
            
    return get_figure_output(fig, format=format)

async def create_dashboard(plots: List[Dict[str, Any]], layout: List[int] = [2, 2], width: int = 1200, height: int = 800, format: str = 'png') -> str:
    """
    Create a subplot dashboard.
    plots: List of dicts with keys: type, x, y, data (DataInput), etc.
    """
    rows, cols = layout
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[p.get('title', '') for p in plots])
    
    for i, pdef in enumerate(plots):
        if i >= rows * cols: break
        
        row_idx = (i // cols) + 1
        col_idx = (i % cols) + 1
        
        ptype = pdef.get('type', 'scatter')
        df = parse_data_frame(pdef.get('data'))
        x = pdef.get('x')
        y = pdef.get('y')
        
        if ptype == 'scatter':
            trace = go.Scatter(x=df[x], y=df[y], mode='markers', name=pdef.get('title'))
            fig.add_trace(trace, row=row_idx, col=col_idx)
        elif ptype == 'line':
            trace = go.Scatter(x=df[x], y=df[y], mode='lines', name=pdef.get('title'))
            fig.add_trace(trace, row=row_idx, col=col_idx)
        elif ptype == 'bar':
            trace = go.Bar(x=df[x], y=df[y], name=pdef.get('title'))
            fig.add_trace(trace, row=row_idx, col=col_idx)
    
    fig.update_layout(width=width, height=height, showlegend=False)
    return get_figure_output(fig, format=format)
