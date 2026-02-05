import yt_dlp
from typing import List, Dict, Any
from mcp_servers.ytdlp_server.tools import core_ops, info_ops

def bulk_get_info(urls: List[str]) -> Dict[str, Any]:
    """Metadata for list of URLs."""
    results = {}
    for url in urls:
        try:
            results[url] = info_ops.get_video_info(url)
        except Exception as e:
            results[url] = {"error": str(e)}
    return results

def bulk_download_videos(urls: List[str]) -> str:
    """Download list of URLs."""
    opts = core_ops.get_default_options()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
        return f"Processed {len(urls)} URLs."
    except Exception as e:
        return f"Error: {e}"

def bulk_download_audio(urls: List[str]) -> str:
    """Download audio for list of URLs."""
    opts = core_ops.get_default_options()
    opts.update({
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
    })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
        return f"Processed {len(urls)} URLs for audio."
    except Exception as e:
        return f"Error: {e}"

def verify_links(urls: List[str]) -> Dict[str, bool]:
    """Check if list of links is valid/live."""
    results = {}
    opts = core_ops.get_default_options()
    opts["extract_flat"] = True
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        for url in urls:
            try:
                ydl.extract_info(url, download=False)
                results[url] = True
            except:
                results[url] = False
    return results

def get_common_metadata_bulk(urls: List[str]) -> List[Dict[str, Any]]:
    """Get Title/Duration for list (fast)."""
    results = []
    # Can we pass list to extract_info? No, single URL usually.
    # Reuse single extractor but loop
    for url in urls:
        try:
            # Use specific info_ops if available, or lightweight extract
            title = info_ops.get_video_title(url)
            dur = info_ops.get_duration(url)
            results.append({"url": url, "title": title, "duration": dur})
        except:
            results.append({"url": url, "error": "failed"})
    return results

def bulk_search_and_download(queries: List[str]) -> str:
    """Search multiple terms and download top result for each."""
    # yt-dlp can handle "ytsearch:query" in download list
    search_urls = [f"ytsearch1:{q}" for q in queries]
    return bulk_download_videos(search_urls)
