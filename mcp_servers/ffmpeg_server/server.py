
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "ffmpeg-python",
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    core_ops, info_ops, convert_ops, filter_ops, bulk_ops, super_ops
)
import structlog
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("ffmpeg_server", dependencies=["pandas", "ffmpeg-python"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def check_ffmpeg_available() -> bool: 
    """CHECKS ffmpeg. [ACTION]
    
    [RAG Context]
    Verify if FFmpeg is installed and accessible.
    Returns boolean.
    """
    return core_ops.check_ffmpeg_available()

@mcp.tool()
def get_ffmpeg_version() -> str: 
    """FETCHES version. [ACTION]
    
    [RAG Context]
    Get installed FFmpeg version.
    Returns version string.
    """
    return core_ops.get_ffmpeg_version()

@mcp.tool()
def set_output_dir(path: str) -> str: 
    """SETS output dir. [ACTION]
    
    [RAG Context]
    Set default directory for output files.
    Returns status string.
    """
    return core_ops.set_output_dir(path)

@mcp.tool()
def validate_media_file(path: str) -> Dict[str, Any]: 
    """VALIDATES media. [ACTION]
    
    [RAG Context]
    Check if file exists and is a valid media file.
    Returns validation dict.
    """
    return core_ops.validate_media_file(path)

@mcp.tool()
def get_codecs() -> str: 
    """LISTS codecs. [ACTION]
    
    [RAG Context]
    List all supported codecs.
    Returns list string.
    """
    return core_ops.get_codecs()

# ==========================================
# 2. Info Extraction
# ==========================================
@mcp.tool()
def probe_file(path: str) -> Dict[str, Any]: 
    """PROBES file. [ACTION]
    
    [RAG Context]
    Get detailed media metadata (ffprobe).
    Returns JSON dict.
    """
    return info_ops.probe_file(path)

@mcp.tool()
def get_duration(path: str) -> float: 
    """FETCHES duration. [ACTION]
    
    [RAG Context]
    Get duration in seconds.
    Returns float.
    """
    return info_ops.get_duration(path)

@mcp.tool()
def get_resolution(path: str) -> str: 
    """FETCHES resolution. [ACTION]
    
    [RAG Context]
    Get video resolution (e.g., 1920x1080).
    Returns string.
    """
    return info_ops.get_resolution(path)

@mcp.tool()
def get_fps(path: str) -> str: 
    """FETCHES framerate. [ACTION]
    
    [RAG Context]
    Get video framerate (FPS).
    Returns string.
    """
    return info_ops.get_fps(path)

@mcp.tool()
def get_audio_info(path: str) -> Dict[str, Any]: 
    """FETCHES audio info. [ACTION]
    
    [RAG Context]
    Get audio stream details (codec, bitrate).
    Returns JSON dict.
    """
    return info_ops.get_audio_info(path)

@mcp.tool()
def get_stream_count(path: str) -> Dict[str, int]: 
    """COUNTS streams. [ACTION]
    
    [RAG Context]
    Count video, audio, and subtitle streams.
    Returns count dict.
    """
    return info_ops.get_stream_count(path)

@mcp.tool()
def get_video_codec(path: str) -> str: 
    """FETCHES video codec. [ACTION]
    
    [RAG Context]
    Get video codec name (e.g., h264).
    Returns string.
    """
    return info_ops.get_video_codec(path)

@mcp.tool()
def count_frames(path: str) -> int: 
    """COUNTS frames. [ACTION]
    
    [RAG Context]
    Count total number of frames in video.
    Returns integer.
    """
    return info_ops.count_frames(path)

@mcp.tool()
def detect_silence(path: str, noise_db: str = "-30dB", duration: float = 1.0) -> str: 
    """DETECTS silence. [ACTION]
    
    [RAG Context]
    Find silent periods in audio.
    Returns report string.
    """
    return info_ops.detect_silence(path, noise_db, duration)

@mcp.tool()
def detect_black_frames(path: str) -> str: 
    """DETECTS black frames. [ACTION]
    
    [RAG Context]
    Find black frames in video.
    Returns report string.
    """
    return info_ops.detect_black_frames(path)

# ==========================================
# 3. Basic Conversion
# ==========================================
@mcp.tool()
def convert_format(input_path: str, output_path: str) -> str: 
    """CONVERTS format. [ACTION]
    
    [RAG Context]
    Convert media file to different format.
    Returns report string.
    """
    return convert_ops.convert_format(input_path, output_path)

@mcp.tool()
def extract_audio(input_path: str, output_path: str = None, format: str = "mp3") -> str: 
    """EXTRACTS audio. [ACTION]
    
    [RAG Context]
    Extract audio track from video.
    Returns output path.
    """
    return convert_ops.extract_audio(input_path, output_path, format)

@mcp.tool()
def trim_video(input_path: str, start_time: str, end_time: str, output_path: str) -> str: 
    """TRIMS video. [ACTION]
    
    [RAG Context]
    Cut video segment by start/end time.
    Returns output path.
    """
    return convert_ops.trim_video(input_path, start_time, end_time, output_path)

@mcp.tool()
def resize_video(input_path: str, width: int, output_path: str) -> str: 
    """RESIZES video. [ACTION]
    
    [RAG Context]
    Resize video width (maintains aspect ratio).
    Returns output path.
    """
    return convert_ops.resize_video(input_path, width, output_path)

@mcp.tool()
def compress_video(input_path: str, output_path: str, crf: int = 23) -> str: 
    """COMPRESSES video. [ACTION]
    
    [RAG Context]
    Compress video using CRF (Constant Rate Factor).
    Returns output path.
    """
    return convert_ops.compress_video(input_path, output_path, crf)

@mcp.tool()
def change_fps(input_path: str, output_path: str, fps: int) -> str: 
    """CHANGES framerate. [ACTION]
    
    [RAG Context]
    Change video framerate.
    Returns output path.
    """
    return convert_ops.change_fps(input_path, output_path, fps)

@mcp.tool()
def rotate_video(input_path: str, output_path: str, rotation: str = "clock") -> str: 
    """ROTATES video. [ACTION]
    
    [RAG Context]
    Rotate video (clock, cclock, 180).
    Returns output path.
    """
    return convert_ops.rotate_video(input_path, output_path, rotation)

@mcp.tool()
def remove_audio(input_path: str, output_path: str) -> str: 
    """REMOVES audio. [ACTION]
    
    [RAG Context]
    Remove audio track from video.
    Returns output path.
    """
    return convert_ops.remove_audio(input_path, output_path)

@mcp.tool()
def replace_audio(video_path: str, audio_path: str, output_path: str) -> str: 
    """REPLACES audio. [ACTION]
    
    [RAG Context]
    Replace audio track in video.
    Returns output path.
    """
    return convert_ops.replace_audio(video_path, audio_path, output_path)

@mcp.tool()
def extract_frames(input_path: str, output_pattern: str = "frame_%04d.png", fps: int = 1) -> str: 
    """EXTRACTS frames. [ACTION]
    
    [RAG Context]
    Extract video frames as images.
    Returns output pattern.
    """
    return convert_ops.extract_frames(input_path, output_pattern, fps)

# ==========================================
# 4. Filters & Effects
# ==========================================
# ==========================================
# 4. Filters & Effects
# ==========================================
@mcp.tool()
def crop_video(input_path: str, x: int, y: int, width: int, height: int, output_path: str) -> str: 
    """CROPS video. [ACTION]
    
    [RAG Context]
    Crop video to specific dimensions/position.
    Returns output path.
    """
    return filter_ops.crop_video(input_path, x, y, width, height, output_path)

@mcp.tool()
def mirror_video(input_path: str, output_path: str) -> str: 
    """MIRRORS video. [ACTION]
    
    [RAG Context]
    Flip video horizontally.
    Returns output path.
    """
    return filter_ops.mirror_video(input_path, output_path)

@mcp.tool()
def grayscale_video(input_path: str, output_path: str) -> str: 
    """GRAYSCALES video. [ACTION]
    
    [RAG Context]
    Convert video to black and white.
    Returns output path.
    """
    return filter_ops.grayscale_video(input_path, output_path)

@mcp.tool()
def adjust_brightness_contrast(input_path: str, brightness: float, contrast: float, output_path: str) -> str: 
    """ADJUSTS image. [ACTION]
    
    [RAG Context]
    Modify video brightness and contrast.
    Returns output path.
    """
    return filter_ops.adjust_brightness_contrast(input_path, brightness, contrast, output_path)

@mcp.tool()
def speed_up_video(input_path: str, factor: float, output_path: str) -> str: 
    """SPEEDS up. [ACTION]
    
    [RAG Context]
    Change video playback speed.
    Returns output path.
    """
    return filter_ops.speed_up_video(input_path, factor, output_path)

@mcp.tool()
def overlay_image(video_path: str, image_path: str, x: int, y: int, output_path: str) -> str: 
    """OVERLAYS image. [ACTION]
    
    [RAG Context]
    Place an image on top of video at x,y.
    Returns output path.
    """
    return filter_ops.overlay_image(video_path, image_path, x, y, output_path)

@mcp.tool()
def draw_text(input_path: str, text: str, x: int, y: int, fontsize: int = 24, fontcolor: str = "white", output_path: str = None) -> str: 
    """DRAWS text. [ACTION]
    
    [RAG Context]
    Burn text onto video at x,y.
    Returns output path.
    """
    return filter_ops.draw_text(input_path, text, x, y, fontsize, fontcolor, output_path)

@mcp.tool()
def fade_in_out(input_path: str, fade_in_len: int, fade_out_len: int, total_duration: int, output_path: str) -> str: 
    """APPLIES fade. [ACTION]
    
    [RAG Context]
    Add fade-in and fade-out effects.
    Returns output path.
    """
    return filter_ops.fade_in_out(input_path, fade_in_len, fade_out_len, total_duration, output_path)

@mcp.tool()
def reverse_video(input_path: str, output_path: str) -> str: 
    """REVERSES video. [ACTION]
    
    [RAG Context]
    Reverse video playback.
    Returns output path.
    """
    return filter_ops.reverse_video(input_path, output_path)

# ==========================================
# 5. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_probe(directory: str) -> List[Dict[str, Any]]: 
    """BULK: Probe. [ACTION]
    
    [RAG Context]
    Get metadata for all media in directory.
    Returns list of dicts.
    """
    return bulk_ops.bulk_probe(directory)

@mcp.tool()
def bulk_convert(directory: str, target_ext: str = ".mp4") -> str: 
    """BULK: Convert. [ACTION]
    
    [RAG Context]
    Convert all media in directory to format.
    Returns report string.
    """
    return bulk_ops.bulk_convert(directory, target_ext)

@mcp.tool()
def bulk_extract_audio(directory: str) -> str: 
    """BULK: Extract Audio. [ACTION]
    
    [RAG Context]
    Extract audio from all videos in directory.
    Returns report string.
    """
    return bulk_ops.bulk_extract_audio(directory)

@mcp.tool()
def bulk_generate_thumbnails(directory: str) -> str: 
    """BULK: Thumbnails. [ACTION]
    
    [RAG Context]
    Generate thumbnails for all videos.
    Returns report string.
    """
    return bulk_ops.bulk_generate_thumbnails(directory)

@mcp.tool()
def get_total_duration(directory: str) -> float: 
    """CALCULATES total duration. [ACTION]
    
    [RAG Context]
    Sum duration of all media in directory.
    Returns float seconds.
    """
    return bulk_ops.get_total_duration(directory)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def create_slideshow(image_dir: str, output_path: str, fps: int = 1) -> str: 
    """CREATES slideshow. [ACTION]
    
    [RAG Context]
    Create video from directory of images.
    Returns output path.
    """
    return super_ops.create_slideshow(image_dir, output_path, fps)

@mcp.tool()
def concat_videos(video_paths: List[str], output_path: str) -> str: 
    """CONCATENATES videos. [ACTION]
    
    [RAG Context]
    Join multiple videos sequentially.
    Returns output path.
    """
    return super_ops.concat_videos(video_paths, output_path)

@mcp.tool()
def grid_layout_videos(video_paths: List[str], output_path: str) -> str: 
    """CREATES video grid. [ACTION]
    
    [RAG Context]
    Combine videos into a grid layout (2x2, etc).
    Returns output path.
    """
    return super_ops.grid_layout_videos(video_paths, output_path)

@mcp.tool()
def create_gif_preview(input_path: str, start_time: int, duration: int, output_path: str) -> str: 
    """CREATES gif preview. [ACTION]
    
    [RAG Context]
    Create animated GIF from video segment.
    Returns output path.
    """
    return super_ops.create_gif_preview(input_path, start_time, duration, output_path)

@mcp.tool()
def split_video_by_time(input_path: str, segment_time: int, output_pattern: str = "out%03d.mp4") -> str: 
    """SPLITS video. [ACTION]
    
    [RAG Context]
    Split video into equal time segments.
    Returns output pattern.
    """
    return super_ops.split_video_by_time(input_path, segment_time, output_pattern)

@mcp.tool()
def create_wave_visualizer(audio_path: str, output_path: str) -> str: 
    """VISUALIZES audio. [ACTION]
    
    [RAG Context]
    Create video visualization of audio waveform.
    Returns output path.
    """
    return super_ops.create_wave_visualizer(audio_path, output_path)

if __name__ == "__main__":
    mcp.run()