from mcp_servers.matplotlib_server.tools.core_ops import parse_vector, get_figure_as_base64
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def create_mosaic(layout: str, plots: Dict[str, Dict[str, Any]], figsize: List[int] = [12, 8], title: Optional[str] = None) -> str:
    """
    Create a complex layout using ASCII art (subplot_mosaic).
    
    Args:
        layout: String defining layout, e.g., "AAB\nCCD"
        plots: Dict mapping layout keys to plot definitions.
               Example: {"A": {"type": "line", "x": [...], "y": [...]}, "B": ...}
    """
    # layout string needs to be formatted correctly (rows separated by newlines or list/list)
    # If passed as "AAB;CCD" convert to list or newline
    if ";" in layout:
        layout_def = [row.strip() for row in layout.split(";")]
    else:
        layout_def = layout # matplotlib accepts "AAB\nCCD" string

    fig, axes = plt.subplot_mosaic(layout_def, figsize=tuple(figsize))
    if title: fig.suptitle(title)
        
    for key, ax in axes.items():
        if key in plots:
            pdef = plots[key]
            ptype = pdef.get('type', 'line')
            x = parse_vector(pdef.get('x'))
            y = parse_vector(pdef.get('y'))
            ptitle = pdef.get('title')
            
            if ptitle: ax.set_title(ptitle)
            
            if ptype == 'line':
                ax.plot(x, y, color=pdef.get('color', 'blue'))
            elif ptype == 'bar':
                ax.bar(x, y, color=pdef.get('color', 'blue'))
            elif ptype == 'scatter':
                ax.scatter(x, y, color=pdef.get('color', 'blue'))
            elif ptype == 'hist':
                ax.hist(x, color=pdef.get('color', 'blue'))
            elif ptype == 'text':
                ax.text(0.5, 0.5, pdef.get('text', ''), ha='center', va='center')
                ax.axis('off')

    plt.tight_layout()
    return get_figure_as_base64(fig)
