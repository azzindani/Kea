# 🔍 Search Server (MCP)

The **Search Server** is the primary discovery engine for Kea. It provides high-quality web and news search capabilities by integrating with major search providers like Tavily and Brave Search.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `web_search` | General web search. Returns relevant URLs, titles, and snippets. Supports `basic` and `advanced` (deeper) search modes. |
| `news_search` | News-specific search with date filtering. Allows narrowing results to the last N days. |

## 🏗️ Implementation

- **Provider Agnostic**: Logic is designed to work with various search APIs (Tavily, Brave, etc.) through a unified interface.
- **Tavily Support**: Optimized for AI research, providing cleaned content and better relevance for complex queries.
- **Async Execution**: Searches are performed asynchronously to maintain high throughput in multi-agent swarms.

## ⚙️ Configuration

The server requires one of the following API keys in the environment:
- `TAVILY_API_KEY`: For Tavily-based search.
- `BRAVE_API_KEY`: For Brave Search (if configured).
