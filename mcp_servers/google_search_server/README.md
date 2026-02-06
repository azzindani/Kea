# 🔌 Google Search Server

The `google_search_server` is an MCP server providing tools for **Google Search Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `search_google` | Execute search google operation | `query: str, num: int = 100000, lang: str = "en", region: str = "us"` |
| `search_basic` | Execute search basic operation | `query: str, num: int = 100000` |
| `search_safe` | Execute search safe operation | `query: str, num: int = 100000` |
| `search_images` | Execute search images operation | `query: str, num: int = 100000` |
| `search_videos` | Execute search videos operation | `query: str, num: int = 100000` |
| `search_past_hour` | Execute search past hour operation | `query: str, num: int = 100000` |
| `search_past_day` | Execute search past day operation | `query: str, num: int = 100000` |
| `search_past_week` | Execute search past week operation | `query: str, num: int = 100000` |
| `search_past_month` | Execute search past month operation | `query: str, num: int = 100000` |
| `search_past_year` | Execute search past year operation | `query: str, num: int = 100000` |
| `search_region` | Execute search region operation | `query: str, region: str, num: int = 100000` |
| `search_us` | Execute search us operation | `query: str, num: int = 100000` |
| `search_uk` | Execute search uk operation | `query: str, num: int = 100000` |
| `search_language` | Execute search language operation | `query: str, lang: str, num: int = 100000` |
| `find_pdf` | Execute find pdf operation | `query: str, num: int = 100000` |
| `find_doc` | Execute find doc operation | `query: str, num: int = 100000` |
| `find_xls` | Execute find xls operation | `query: str, num: int = 100000` |
| `find_ppt` | Execute find ppt operation | `query: str, num: int = 100000` |
| `find_txt` | Execute find txt operation | `query: str, num: int = 100000` |
| `find_csv` | Execute find csv operation | `query: str, num: int = 100000` |
| `find_json` | Execute find json operation | `query: str, num: int = 100000` |
| `find_xml` | Execute find xml operation | `query: str, num: int = 100000` |
| `find_config_files` | Execute find config files operation | `query: str = "", num: int = 100000` |
| `find_env_files` | Execute find env files operation | `query: str = "", num: int = 100000` |
| `find_database_dumps` | Execute find database dumps operation | `query: str = "", num: int = 100000` |
| `find_log_files` | Execute find log files operation | `query: str = "", num: int = 100000` |
| `find_backup_files` | Execute find backup files operation | `query: str = "", num: int = 100000` |
| `site_search` | Execute site search operation | `query: str, domain: str, num: int = 100000` |
| `exclude_site` | Execute exclude site operation | `query: str, domain_to_exclude: str, num: int = 100000` |
| `find_subdomains` | Execute find subdomains operation | `domain: str, num: int = 100000` |
| `find_login_pages` | Execute find login pages operation | `domain: str, num: int = 100000` |
| `find_admin_pages` | Execute find admin pages operation | `domain: str, num: int = 100000` |
| `find_wordpress` | Execute find wordpress operation | `domain: str, num: int = 100000` |
| `find_directory_indices` | Execute find directory indices operation | `domain: str = "", num: int = 100000` |
| `intitle_search` | Execute intitle search operation | `query: str, num: int = 100000` |
| `allintitle_search` | Execute allintitle search operation | `query: str, num: int = 100000` |
| `inurl_search` | Execute inurl search operation | `query: str, num: int = 100000` |
| `allinurl_search` | Execute allinurl search operation | `query: str, num: int = 100000` |
| `intext_search` | Execute intext search operation | `query: str, num: int = 100000` |
| `related_search` | Execute related search operation | `domain: str, num: int = 100000` |
| `cache_search` | Execute cache search operation | `domain: str, num: int = 100000` |
| `find_social_media` | Execute find social media operation | `query: str, num: int = 100000` |
| `find_linkedin_profiles` | Execute find linkedin profiles operation | `query: str, num: int = 100000` |
| `find_public_trello` | Execute find public trello operation | `query: str, num: int = 100000` |
| `find_public_drive` | Execute find public drive operation | `query: str, num: int = 100000` |
| `check_ranking` | Execute check ranking operation | `query: str, target_domain: str, num_check: int = 100000` |
| `get_domains` | Execute get domains operation | `query: str, num: int = 100000` |
| `competitor_discovery` | Execute competitor discovery operation | `domain: str, num: int = 100000` |
| `monitor_brand` | Execute monitor brand operation | `brand_name: str, num: int = 100000` |
| `bulk_search` | Execute bulk search operation | `queries: List[str], num_per_query: int = 100000, delay: float = 2.0` |
| `bulk_dork` | Execute bulk dork operation | `dork_template: str, targets: List[str], num: int = 100000` |
| `search_news` | Execute search news operation | `query: str, num: int = 100000` |
| `search_finance_news` | Execute search finance news operation | `query: str, num: int = 100000` |
| `search_tech_news` | Execute search tech news operation | `query: str, num: int = 100000` |
| `get_headlines_topic` | Execute get headlines topic operation | `topic: str, num: int = 100000` |

## 📦 Dependencies

The following packages are required:
- `googlesearch-python`
- `beautifulsoup4`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.google_search_server.server
```
