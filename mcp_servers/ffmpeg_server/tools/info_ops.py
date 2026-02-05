import ffmpeg
import json
from typing import Dict, Any, List

def probe_file(path: str) -> Dict[str, Any]:
    """Full JSON probe (`ffprobe`)."""
    try:
        return ffmpeg.probe(path)
    except ffmpeg.Error as e:
        return {"error": e.stderr.decode("utf-8") if e.stderr else str(e)}

def get_duration(path: str) -> float:
    """Duration in seconds."""
    info = probe_file(path)
    if "format" in info:
        return float(info["format"].get("duration", 0))
    return 0.0

def get_resolution(path: str) -> str:
    """Width x Height."""
    info = probe_file(path)
    video = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), None)
    if video:
        return f"{video.get('width')}x{video.get('height')}"
    return "unknown"

def get_fps(path: str) -> str:
    """Frame rate (e.g. 30/1 or 30)."""
    info = probe_file(path)
    video = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), None)
    return video.get("r_frame_rate", "0/0") if video else "0/0"

def get_audio_info(path: str) -> Dict[str, Any]:
    """Sample rate, channels, codec."""
    info = probe_file(path)
    audio = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), None)
    if audio:
        return {
            "codec_name": audio.get("codec_name"),
            "channels": audio.get("channels"),
            "sample_rate": audio.get("sample_rate"),
            "bit_rate": audio.get("bit_rate")
        }
    return {"error": "No audio stream found"}

def get_stream_count(path: str) -> Dict[str, int]:
    """Number of video/audio/sub streams."""
    info = probe_file(path)
    counts = {"video": 0, "audio": 0, "subtitle": 0, "data": 0}
    for s in info.get("streams", []):
        t = s.get("codec_type", "data")
        counts[t] = counts.get(t, 0) + 1
    return counts

def get_video_codec(path: str) -> str:
    """e.g. h264."""
    info = probe_file(path)
    video = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), None)
    return video.get("codec_name", "unknown") if video else "none"

def count_frames(path: str) -> int:
    """Estimate frame count (parse or scan)."""
    # Try reading from stream tags first
    info = probe_file(path)
    video = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), None)
    if video and "nb_frames" in video:
        return int(video["nb_frames"])
    
    # Fallback usually requires full scan (slow), skipping for now to keep tool fast
    return -1

def detect_silence(path: str, noise_db: str = "-30dB", duration: float = 1.0) -> str:
    """Check for silence periods (volumedetect)."""
    # volumedetect filter
    try:
        out, err = (
            ffmpeg
            .input(path)
            .filter('volumedetect')
            .output('null', f='null')
            .run(capture_stdout=True, capture_stderr=True)
        )
        return err.decode('utf-8') # User has to parse log. 
    except ffmpeg.Error as e:
        return str(e.stderr)

def detect_black_frames(path: str) -> str:
    """Check for black frames (blackdetect)."""
    try:
        out, err = (
            ffmpeg
            .input(path)
            .filter('blackdetect')
            .output('null', f='null')
            .run(capture_stdout=True, capture_stderr=True)
        )
        return err.decode('utf-8')
    except ffmpeg.Error as e:
        return str(e.stderr)
