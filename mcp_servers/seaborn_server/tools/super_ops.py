from mcp_servers.seaborn_server.tools.core_ops import parse_data_frame, get_figure_as_base64, DataInput
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def auto_plot(data: DataInput, x: str, y: Optional[str] = None) -> str:
    """
    Intelligently select and draw a plot based on the variables.
    - 1 Numeric: Distplot
    - 2 Numeric: Scatter/Reg
    - 1 Numeric + 1 Cat: Box/Violin
    - 2 Cat: Count/Heatmap
    """
    df = parse_data_frame(data)
    
    # Check types
    is_x_num = pd.api.types.is_numeric_dtype(df[x])
    is_y_num = pd.api.types.is_numeric_dtype(df[y]) if y else False
    
    plt.figure()
    
    if y is None:
        if is_x_num:
            sns.histplot(data=df, x=x, kde=True) # Univariate Dist
        else:
            sns.countplot(data=df, x=x) # Univariate Count
    else:
        if is_x_num and is_y_num:
            sns.scatterplot(data=df, x=x, y=y) # Bivariate numeric
        elif (not is_x_num) and is_y_num:
            sns.boxplot(data=df, x=x, y=y) # Cat vs Num
        elif is_x_num and (not is_y_num):
            sns.boxplot(data=df, x=y, y=x, orient='h') # Num vs Cat
        else:
            # Cat vs Cat - difficult with basic plots, maybe heatmap of crosstab?
            ct = pd.crosstab(df[x], df[y])
            sns.heatmap(ct, annot=True, fmt='d')
            
    return get_figure_as_base64()

async def create_dashboard(data: DataInput, plots: List[Dict[str, Any]], layout: List[int] = [2, 2], figsize: List[int] = [15, 10]) -> str:
    """
    Create a grid of Seaborn plots.
    """
    df = parse_data_frame(data)
    rows, cols = layout
    fig, axes = plt.subplots(rows, cols, figsize=tuple(figsize))
    axes_flat = axes.flatten()
    
    for i, pdef in enumerate(plots):
        if i >= len(axes_flat): break
        ax = axes_flat[i]
        
        ptype = pdef.get('type')
        x = pdef.get('x')
        y = pdef.get('y')
        hue = pdef.get('hue')
        title = pdef.get('title')
        
        if ptype == 'hist':
            sns.histplot(data=df, x=x, hue=hue, ax=ax)
        elif ptype == 'scatter':
            sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
        elif ptype == 'box':
            sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax)
        elif ptype == 'bar':
            sns.barplot(data=df, x=x, y=y, hue=hue, ax=ax)
        elif ptype == 'count':
            sns.countplot(data=df, x=x, hue=hue, ax=ax)
            
        if title: ax.set_title(title)
        
    plt.tight_layout()
    return get_figure_as_base64(fig)
