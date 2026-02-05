from mcp_servers.matplotlib_server.tools.core_ops import setup_figure, get_figure_as_base64
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Any, List, Optional, Union

async def draw_shapes(shapes: List[Dict[str, Any]], title: Optional[str] = None, x_lim: List[float] = [0, 10], y_lim: List[float] = [0, 10], figsize: List[int] = [10, 8]) -> str:
    """
    Draw geometric shapes.
    Shapes dict keys: type (rect, circle, polygon, arrow), params...
    """
    fig, ax = setup_figure(title, None, None, tuple(figsize))
    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)
    ax.set_aspect('equal')
    
    for s in shapes:
        stype = s.get('type')
        color = s.get('color', 'blue')
        alpha = s.get('alpha', 0.5)
        
        if stype == 'rect':
            xy = s.get('xy', (0,0))
            width = s.get('width', 1)
            height = s.get('height', 1)
            angle = s.get('angle', 0.0)
            p = patches.Rectangle(xy, width, height, angle=angle, linewidth=1, facecolor=color, alpha=alpha)
            ax.add_patch(p)
            
        elif stype == 'circle':
            xy = s.get('xy', (5,5))
            radius = s.get('radius', 1)
            p = patches.Circle(xy, radius=radius, facecolor=color, alpha=alpha)
            ax.add_patch(p)
            
        elif stype == 'polygon':
            xy = s.get('points', [[2,2], [4,4], [6,2]])
            p = patches.Polygon(xy, closed=True, facecolor=color, alpha=alpha)
            ax.add_patch(p)
            
        elif stype == 'arrow':
            x, y = s.get('start', (0,0))
            dx, dy = s.get('delta', (1,1))
            width = s.get('width', 0.1)
            p = patches.Arrow(x, y, dx, dy, width=width, color=color, alpha=alpha)
            ax.add_patch(p)
            
    return get_figure_as_base64(fig)
