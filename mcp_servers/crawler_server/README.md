# 🕷️ Crawler Server (MCP)

The **Crawler Server** is a specialized engine for deep website exploration, recursive indexing, and link map discovery. It provides high-performance tools for multi-page crawling with robust oversight of crawling etiquette (robots.txt, delays).

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `web_crawler` | Recursively crawl a website with configurable depth and page limits. Includes automatic domain lock and rate limiting. |
| `sitemap_parser` | Discovers and extracts all URLs from a website's `sitemap.xml` or sitemap index. |
| `link_extractor` | Extracts and classifies all anchor tags on a page (internal vs. external, file types). |
| `robots_checker` | Validates if specific paths are allowed for crawling according to the site's `robots.txt`. |
| `domain_analyzer` | Analyzes a domain's structure (links, forms, images) to inform a crawling strategy. |

## 🏗️ Implementation

Built on `httpx` and `BeautifulSoup4`. The crawler implements a recursive `async` flow with a `semaphore` to manage concurrency and prevent overloading target servers. It handles both `sitemap.xml` and sitemap indices.

## ⚖️ Etiquette

The server is designed to respect common crawling standards:
- **Depth Control**: Prevents infinite loops.
- **Same Domain Lock**: Prevents the crawler from wandering off-site accidentally.
- **Rate Limiting**: Configurable `delay` parameter (default 0.5s).
