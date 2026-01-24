# 🌐 Browser Agent Server (MCP)

The **Browser Agent Server** is designed to mimic human browsing behavior to perform stealthy, high-quality research. It includes tools for navigating the web, validating source credibility, and managing a short-term "search memory" to avoid redundant visits.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `human_like_search` | Performs searches with randomized delays and natural navigation to mimic a human researcher. |
| `source_validator` | Evaluates a website's credibility based on TLD trust, authoritative status, and security protocols. |
| `domain_scorer` | Provides comparative trustworthiness scores for multiple domains. |
| `search_memory_add` | Saves a search result (URL, title, summary) to the local session memory. |
| `search_memory_recall` | Retrieves previously saved results from memory based on relevance. |
| `multi_site_browse` | Concurrently browses multiple URLs (up to 20 parallel) to extract summaries or links. |

## 🏗️ Implementation

The server uses `httpx` and `BeautifulSoup4` for light extraction. It includes a sophisticated "Delay Engine" to prevent rate-limiting and a credibility scoring logic based on academic and institutional trust signals.

## 🧠 Memory System

This server maintains an in-memory `SEARCH_MEMORY` dictionary for the duration of the process. In a production environment, this can be synchronized with the Core **Vault** or **RAG Service**.
