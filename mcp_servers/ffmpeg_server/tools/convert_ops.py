import ffmpeg
import os
from mcp_servers.ffmpeg_server.tools import core_ops

def convert_format(input_path: str, output_path: str) -> str:
    """Transcode (e.g., mkv -> mp4)."""
    if not output_path:
        # Default name
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_converted.mp4"
        
    try:
        ffmpeg.input(input_path).output(output_path).run(overwrite_output=True)
        return f"Converted to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8') if e.stderr else str(e)}"

def extract_audio(input_path: str, output_path: str = None, format: str = "mp3") -> str:
    """Save audio track as mp3/wav/aac."""
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}.{format}"
    
    try:
        ffmpeg.input(input_path).output(output_path, acodec='libmp3lame' if format=='mp3' else 'copy').run(overwrite_output=True)
        return f"Extracted audio to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def trim_video(input_path: str, start_time: str, end_time: str, output_path: str) -> str:
    """Cut from Start to End (time string '00:00:10')."""
    try:
        (
            ffmpeg
            .input(input_path, ss=start_time, to=end_time)
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Trimmed to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def resize_video(input_path: str, width: int, output_path: str) -> str:
    """Change resolution (scale width, auto height)."""
    try:
        (
            ffmpeg
            .input(input_path)
            .filter('scale', width, -1)
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Resized to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def compress_video(input_path: str, output_path: str, crf: int = 23) -> str:
    """Reduce CRF/Bitrate (CRF 0-51, default 23. Higher is smaller file/worse quality)."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, crf=crf, vcodec='libx264')
            .run(overwrite_output=True)
        )
        return f"Compressed to {output_path} (CRF {crf})"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def change_fps(input_path: str, output_path: str, fps: int) -> str:
    """Resample frame rate."""
    try:
        (
            ffmpeg
            .input(input_path)
            .filter('fps', fps=fps)
            .output(output_path)
            .run(overwrite_output=True)
        )
        return f"Changed FPS to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def rotate_video(input_path: str, output_path: str, rotation: str = "clock") -> str:
    """Rotate (transpose). 'clock' (90), 'cclock' (-90), 'clock_flip', '180'."""
    transpose_map = {
        "clock": 1,
        "cclock": 2,
        "clock_flip": 3,
        "cclock_flip": 0,
    }
    # 180 is transpose=1,transpose=1
    
    try:
        if rotation == "180":
             (
                ffmpeg
                .input(input_path)
                .filter('transpose', 1)
                .filter('transpose', 1)
                .output(output_path)
                .run(overwrite_output=True)
            )
        else:
            val = transpose_map.get(rotation, 1)
            (
                ffmpeg
                .input(input_path)
                .filter('transpose', val)
                .output(output_path)
                .run(overwrite_output=True)
            )
        return f"Rotated to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def remove_audio(input_path: str, output_path: str) -> str:
    """Mute video (remove audio track)."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, an=None)
            .run(overwrite_output=True)
        )
        return f"Removed audio to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def replace_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """Swap audio track with external file."""
    try:
        v = ffmpeg.input(video_path)
        a = ffmpeg.input(audio_path)
        (
            ffmpeg
            .output(v['v'], a['a'], output_path)
            .run(overwrite_output=True)
        )
        return f"Replaced audio to {output_path}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"

def extract_frames(input_path: str, output_pattern: str = "frame_%04d.png", fps: int = 1) -> str:
    """Save N frames as images (fps=1 means 1 frame per second)."""
    try:
        (
            ffmpeg
            .input(input_path)
            .filter('fps', fps=fps)
            .output(output_pattern)
            .run(overwrite_output=True)
        )
        return f"Extracted frames to {output_pattern}"
    except ffmpeg.Error as e:
        return f"Error: {e.stderr.decode('utf-8')}"
