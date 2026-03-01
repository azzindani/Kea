# 🔌 Ddg Search Server

The `ddg_search_server` is an MCP server providing tools for **Ddg Search Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `search_text` | Execute search text operation | `query: str, region: str = "wt-wt", safe_search: str = "moderate", time: Optional[str] = None, max_results: int = 10` |
| `search_private` | Execute search private operation | `query: str, max_results: int = 10` |
| `search_answers` | Execute search answers operation | `query: str` |
| `search_suggestions` | Execute search suggestions operation | `query: str, region: str = "wt-wt"` |
| `search_past_day` | Execute search past day operation | `query: str, max_results: int = 10` |
| `search_past_week` | Execute search past week operation | `query: str, max_results: int = 10` |
| `search_past_month` | Execute search past month operation | `query: str, max_results: int = 10` |
| `search_past_year` | Execute search past year operation | `query: str, max_results: int = 10` |
| `search_region` | Execute search region operation | `query: str, region: str, max_results: int = 10` |
| `search_python_docs` | Execute search python docs operation | `query: str, max_results: int = 10` |
| `search_stackoverflow` | Execute search stackoverflow operation | `query: str, max_results: int = 10` |
| `search_images` | Execute search images operation | `query: str, size: Optional[str] = None, type_image: Optional[str] = None, layout: Optional[str] = None, license_image: Optional[str] = None, max_results: int = 10` |
| `find_clipart` | Execute find clipart operation | `query: str, max_results: int = 10` |
| `find_gifs` | Execute find gifs operation | `query: str, max_results: int = 10` |
| `find_transparent` | Execute find transparent operation | `query: str, max_results: int = 10` |
| `find_wallpapers` | Execute find wallpapers operation | `query: str, max_results: int = 10` |
| `find_creative_commons` | Execute find creative commons operation | `query: str, max_results: int = 10` |
| `find_people_images` | Execute find people images operation | `query: str, max_results: int = 10` |
| `find_icons` | Execute find icons operation | `query: str, max_results: int = 10` |
| `find_red_images` | Execute find red images operation | `query: str, max_results: int = 10` |
| `find_blue_images` | Execute find blue images operation | `query: str, max_results: int = 10` |
| `search_videos` | Execute search videos operation | `query: str, resolution: Optional[str] = None, duration: Optional[str] = None, max_results: int = 10` |
| `find_short_videos` | Execute find short videos operation | `query: str, max_results: int = 10` |
| `find_long_videos` | Execute find long videos operation | `query: str, max_results: int = 10` |
| `find_high_res_videos` | Execute find high res videos operation | `query: str, max_results: int = 10` |
| `find_cc_videos` | Execute find cc videos operation | `query: str, max_results: int = 10` |
| `search_news` | Execute search news operation | `query: str, region: str = "wt-wt", max_results: int = 10` |
| `search_news_topic` | Execute search news topic operation | `topic: str, max_results: int = 10` |
| `latest_news` | Execute latest news operation | `query: str, max_results: int = 10` |
| `get_trending` | Execute get trending operation | `max_results: int = 10` |
| `search_places` | Execute search places operation | `query: str, max_results: int = 10` |
| `get_address` | Execute get address operation | `query: str` |
| `find_near_me` | Execute find near me operation | `query: str, max_results: int = 10` |
| `translate_text` | Execute translate text operation | `text: str, to_lang: str = "en"` |
| `identify_language` | Execute identify language operation | `text: str` |
| `bulk_text_search` | Execute bulk text search operation | `queries: List[str], max_results: int = 5` |
| `bulk_image_search` | Execute bulk image search operation | `queries: List[str], max_results: int = 5` |
| `bulk_news_search` | Execute bulk news search operation | `queries: List[str], max_results: int = 5` |

## 📦 Dependencies

The following packages are required:
- `duckduckgo_search`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.ddg_search_server.server
```
