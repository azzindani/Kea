import ffmpeg
import os
from typing import List

def create_slideshow(image_dir: str, output_path: str, fps: int = 1) -> str:
    """Images -> Video. Naming must be sequential e.g. img%03d.jpg usually."""
    # ffmpeg-python glob pattern type
    try:
        (
            ffmpeg
            .input(f"{image_dir}/*.jpg", pattern_type='glob', framerate=fps)
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Slideshow created at {output_path}"
    except ffmpeg.Error as e:
        return f"Error (ensure glob support or naming): {e.stderr}"

def concat_videos(video_paths: List[str], output_path: str) -> str:
    """Merge Video A + Video B + Video C."""
    # Using concat methods
    # inputs = [ffmpeg.input(f) for f in video_paths]
    # ffmpeg.concat(*inputs).output...
    
    # safer to create a file list for concat demuxer if varying codecs, but simple filter concat for same codecs
    inputs = [ffmpeg.input(f) for f in video_paths]
    try:
        (
            ffmpeg
            .concat(*inputs)
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Concatenated to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def grid_layout_videos(video_paths: List[str], output_path: str) -> str:
    """2x2 Grid (requires exactly 4 videos for 2x2, or specialized filter)."""
    # xstack filter
    if len(video_paths) != 4:
        return "Error: strict 4-video grid implemented for now."
    
    inputs = [ffmpeg.input(f) for f in video_paths]
    try:
        # xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0
        (
            ffmpeg
            .filter(inputs, 'xstack', inputs=4, layout='0_0|w0_0|0_h0|w0_h0')
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Grid created at {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def create_gif_preview(input_path: str, start_time: int, duration: int, output_path: str) -> str:
    """Short looped GIF from middle of video."""
    try:
        (
            ffmpeg
            .input(input_path, ss=start_time, t=duration)
            .filter('scale', 320, -1)
            .output(output_path, loop=0)
            .run(overwrite_output=True)
        )
        return f"GIF created at {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def split_video_by_time(input_path: str, segment_time: int, output_pattern: str = "out%03d.mp4") -> str:
    """Chunk video into N second segments (segment muxer)."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_pattern, f='segment', segment_time=segment_time, reset_timestamps=1)
            .run(overwrite_output=True)
        )
        return f"Split to {output_pattern}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def create_wave_visualizer(audio_path: str, output_path: str) -> str:
    """Audio -> Waveform video (showwaves)."""
    try:
        (
            ffmpeg
            .input(audio_path)
            .filter('showwaves', s='1280x720', mode='line')
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Visualizer created at {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"
