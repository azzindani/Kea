# 🕷️ Scraper Server (MCP)

The **Scraper Server** is the primary engine for extracting raw content from the web. It provides both lightweight HTTP fetching for static sites and full-featured headless browser execution for dynamic, JavaScript-heavy applications.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `fetch_url` | Lightweight HTTP GET request. Best for fast extraction of static HTML or text content. |
| `browser_scrape` | Full-browser execution using **Playwright**. Supports waiting for selectors, executing JavaScript, and capturing screenshots. |

## 🏗️ Implementation

- **Playwright (Chromium)**: Powers the `browser_scrape` tool, ensuring it can handle modern web apps (React, Vue, SPA).
- **Stealth Mode**: Includes basic headers and behavior randomization to reduce detection by anti-bot measures.
- **Auto-Installation**: The server attempt to JIT-install Playwright browsers on the first run within its container/environment.

## 🛠️ Performance Tip

Use `fetch_url` whenever possible for speed. Only escalate to `browser_scrape` if the target site requires JavaScript execution or has complex dynamic loading.
