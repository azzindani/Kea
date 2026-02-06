# 🔌 Ytdlp Server

The `ytdlp_server` is an MCP server providing tools for **Ytdlp Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `get_version` | Execute get version operation | `` |
| `update_binary` | Execute update binary operation | `` |
| `set_download_dir` | Execute set download dir operation | `path: str` |
| `set_cookies_file` | Execute set cookies file operation | `path: str` |
| `set_proxy` | Execute set proxy operation | `url: str` |
| `set_user_agent` | Execute set user agent operation | `ua: str` |
| `get_default_options` | Execute get default options operation | `` |
| `get_video_info` | Execute get video info operation | `url: str` |
| `get_video_title` | Execute get video title operation | `url: str` |
| `get_video_description` | Execute get video description operation | `url: str` |
| `get_video_tags` | Execute get video tags operation | `url: str` |
| `get_video_thumbnail_url` | Execute get video thumbnail url operation | `url: str` |
| `get_playlist_info` | Execute get playlist info operation | `url: str, max_items: int = 50` |
| `get_channel_info` | Execute get channel info operation | `url: str, max_items: int = 10` |
| `search_videos` | Execute search videos operation | `query: str, n: int = 5` |
| `get_subtitles_list` | Execute get subtitles list operation | `url: str` |
| `get_view_count` | Execute get view count operation | `url: str` |
| `get_duration` | Execute get duration operation | `url: str` |
| `list_formats` | Execute list formats operation | `url: str` |
| `get_best_video_format` | Execute get best video format operation | `url: str` |
| `get_best_audio_format` | Execute get best audio format operation | `url: str` |
| `get_worst_quality_format` | Execute get worst quality format operation | `url: str` |
| `filter_formats_by_res` | Execute filter formats by res operation | `url: str, height: int` |
| `check_format_availability` | Execute check format availability operation | `url: str, format_id: str` |
| `download_video` | Execute download video operation | `url: str` |
| `download_audio_only` | Execute download audio only operation | `url: str, format: str = "mp3"` |
| `download_specific_format` | Execute download specific format operation | `url: str, format_id: str` |
| `download_thumbnail` | Execute download thumbnail operation | `url: str` |
| `download_subtitles` | Execute download subtitles operation | `url: str, lang: str = "en"` |
| `download_description` | Execute download description operation | `url: str` |
| `download_video_restricted` | Execute download video restricted operation | `url: str, max_height: int = 1080` |
| `download_playlist_indices` | Execute download playlist indices operation | `url: str, indices: str` |
| `download_channel_latest` | Execute download channel latest operation | `url: str, n: int = 5` |
| `download_with_metadata` | Execute download with metadata operation | `url: str` |
| `bulk_get_info` | Execute bulk get info operation | `urls: List[str]` |
| `bulk_download_videos` | Execute bulk download videos operation | `urls: List[str]` |
| `bulk_download_audio` | Execute bulk download audio operation | `urls: List[str]` |
| `verify_links` | Execute verify links operation | `urls: List[str]` |
| `get_common_metadata_bulk` | Execute get common metadata bulk operation | `urls: List[str]` |
| `bulk_search_and_download` | Execute bulk search and download operation | `queries: List[str]` |
| `archive_channel` | Execute archive channel operation | `url: str, download_archive_path: str = "archive.txt"` |
| `sync_playlist` | Execute sync playlist operation | `url: str, download_archive_path: str = "playlist_archive.txt"` |
| `create_audio_library` | Execute create audio library operation | `url: str, output_template: str = "%(artist)s/%(album)s/%(title)s.%(ext)s"` |
| `monitor_new_uploads` | Execute monitor new uploads operation | `url: str, date_after: str` |
| `top_n_by_views` | Execute top n by views operation | `url: str, n: int = 10` |
| `extract_highlights` | Execute extract highlights operation | `url: str, timestamps: List[str]` |
| `metadata_audit` | Execute metadata audit operation | `url: str` |
| `download_best_available_series` | Execute download best available series operation | `urls: List[str]` |
| `find_duplicates_in_playlist` | Execute find duplicates in playlist operation | `url: str` |
| `backup_channel_metadata` | Execute backup channel metadata operation | `url: str, output_file: str` |
| `download_time_range` | Execute download time range operation | `url: str, start_date: str, end_date: str` |

## 📦 Dependencies

The following packages are required:
- `pandas`
- `yt-dlp`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.ytdlp_server.server
```
