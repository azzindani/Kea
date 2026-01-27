import ffmpeg
import os
import glob
from typing import List, Dict, Any
from mcp_servers.ffmpeg_server.tools import core_ops, info_ops

def bulk_probe(directory: str) -> List[Dict[str, Any]]:
    """Info for directory of files."""
    results = []
    for f in os.listdir(directory):
        if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.mp3')):
            full = os.path.join(directory, f)
            meta = info_ops.probe_file(full)
            # slim down
            dur = meta["format"].get("duration", 0) if "format" in meta else 0
            results.append({"filename": f, "duration": dur})
    return results

def bulk_convert(directory: str, target_ext: str = ".mp4") -> str:
    """Convert all videos in folder to target extension."""
    count = 0
    errors = []
    
    files = []
    for ext in ['*.mov', '*.avi', '*.mkv', '*.flv']: # scan common
        files.extend(glob.glob(os.path.join(directory, ext)))
        
    for f in files:
        base = os.path.splitext(f)[0]
        out = base + target_ext
        try:
            ffmpeg.input(f).output(out).run(overwrite_output=True)
            count += 1
        except Exception as e:
            errors.append(f"{f}: {e}")
            
    return f"Converted {count} files. Errors: {len(errors)}"

def bulk_extract_audio(directory: str) -> str:
    """Extract audio from all videos."""
    count = 0
    files = []
    for ext in ['*.mp4', '*.mov']:
        files.extend(glob.glob(os.path.join(directory, ext)))
        
    for f in files:
        base = os.path.splitext(f)[0]
        out = base + ".mp3"
        try:
            ffmpeg.input(f).output(out, acodec='libmp3lame').run(overwrite_output=True)
            count += 1
        except:
            pass
    return f"Extracted audio from {count} files."

def bulk_generate_thumbnails(directory: str) -> str:
    """Create 1 thumb for each video at t=1s."""
    count = 0
    files = []
    for ext in ['*.mp4', '*.mov', '*.mkv']:
        files.extend(glob.glob(os.path.join(directory, ext)))
        
    for f in files:
        out = f + ".jpg"
        try:
             # ss=1, vframes=1
            (
                ffmpeg
                .input(f, ss=1)
                .output(out, vframes=1)
                .run(overwrite_output=True)
            )
            count += 1
        except:
            pass
    return f"Generated {count} thumbnails."

def get_total_duration(directory: str) -> float:
    """Sum duration of all files."""
    total = 0.0
    files = []
    for ext in ['*.mp4', '*.mov', '*.mkv', '*.mp3']:
        files.extend(glob.glob(os.path.join(directory, ext)))
        
    for f in files:
        total += float(info_ops.get_duration(f))
    return total
