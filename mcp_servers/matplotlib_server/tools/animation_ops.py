from mcp_servers.matplotlib_server.tools.core_ops import parse_vector, parse_data_frame, DataInput
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np
import io
import base64
import tempfile
import os
from typing import Dict, Any, List, Optional, Union

async def create_animation(frames_data: List[DataInput], plot_type: str = 'line', x: Optional[DataInput] = None, title: Optional[str] = None, interval: int = 200, figsize: List[int] = [10, 6]) -> str:
    """
    Create a GIF animation from a sequence of data frames.
    
    Args:
        frames_data: List of data for each frame (e.g., Y values for line plot).
        plot_type: 'line', 'scatter', 'bar'.
        x: Optional X values (shared across frames).
    """
    fig, ax = plt.subplots(figsize=tuple(figsize))
    if title: ax.set_title(title)
    
    # Pre-parse shared X
    x_vec = parse_vector(x) if x is not None else None
    
    # Parse all frames to ensure valid data
    parsed_frames = []
    min_y, max_y = float('inf'), float('-inf')
    
    for f in frames_data:
        vec = parse_vector(f)
        parsed_frames.append(vec)
        min_y = min(min_y, vec.min())
        max_y = max(max_y, vec.max())
    
    if x_vec is None:
        x_vec = np.arange(len(parsed_frames[0]))
        
    # Set limits once
    ax.set_xlim(x_vec.min(), x_vec.max())
    ax.set_ylim(min_y - (max_y-min_y)*0.1, max_y + (max_y-min_y)*0.1)
    
    # Init Plot Artist
    if plot_type == 'line':
        artist, = ax.plot([], [], lw=2)
        
        def update(frame_idx):
            y_data = parsed_frames[frame_idx]
            artist.set_data(x_vec, y_data)
            return artist,
            
    elif plot_type == 'scatter':
        artist = ax.scatter([], [])
        
        def update(frame_idx):
            y_data = parsed_frames[frame_idx]
            data = np.stack([x_vec, y_data]).T
            artist.set_offsets(data)
            return artist,
            
    elif plot_type == 'bar':
        # Bars are trickier to animate efficiently (usually remove and re-add patches)
        # Simplified: clear and redraw (slower but works)
        def update(frame_idx):
            ax.clear()
            if title: ax.set_title(title)
            ax.set_ylim(min_y, max_y)
            y_data = parsed_frames[frame_idx]
            ax.bar(x_vec, y_data)
            return ax.patches
    
    ani = animation.FuncAnimation(fig, update, frames=len(parsed_frames), interval=interval, blit=(plot_type!='bar'))
    
    # Save to GIF text (base64)
    # Requires Pillow writer usually available
    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
        ani.save(tmp.name, writer='pillow', fps=1000//interval)
        with open(tmp.name, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
        
    plt.close(fig)
    return data
