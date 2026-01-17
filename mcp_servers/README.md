# MCP Servers ("The Tools")

This directory contains the **Model Context Protocol (MCP)** compliant microservices that provide capabilities to the Kea Orchestrator. Each server isolates dependencies (e.g., browser drivers, analysis libraries) to ensure system stability.

## 🏗️ Architecture

Kea uses a "Hub and Spoke" tool architecture. The Orchestrator (Client) connects to these servers via stdio or HTTP/SSE.

## 🧩 Server Catalog

### 1. Core Servers
Essential capabilities required for the basic research loop.

| Server Name | Directory | Description | Key Tools |
|:------------|:----------|:------------|:----------|
| **Scraper** | `scraper_server/` | The primary interface for web interaction. Handles HTML parsing and PDF extraction. | `fetch_url`, `pdf_extract` |
| **Search** | `search_server/` | Connectivity to search APIs (DuckDuckGo, Google, etc.). | `web_search`, `news_search` |
| **Python** | `python_server/` | A sandboxed Docker/E2B environment for code execution. | `execute_code`, `dataframe_ops`, `sql_query` |
| **Vision** | `vision_server/` | OCR and Chart Analysis using Multimodal LLMs. | `read_image`, `analyze_chart` |

### 2. Data & Analytics Servers
Specialized servers for handling quantitative data.

| Server Name | Directory | Description | Key Tools |
|:------------|:----------|:------------|:----------|
| **Data Sources**| `data_sources_server/`| Access to external financial APIs (IDX, Yahoo Finance, AlphaVantage). | `get_stock_price`, `get_financials` |
| **Analytics** | `analytics_server/` | Statistical analysis library (Regression, Correlation). | `calculate_correlation`, `run_regression` |
| **ML** | `ml_server/` | Lightweight machine learning inference (Scikit-Learn). | `predict_trend`, `cluster_data` |
| **Visualization**| `visualization_server/`| Generates charts and graphs (Matplotlib/Plotly). | `create_line_chart`, `create_bar_chart` |

### 3. Domain Servers
Knowledge retrieval for specific domains.

| Server Name | Directory | Description | Key Tools |
|:------------|:----------|:------------|:----------|
| **Academic** | `academic_server/` | Connects to scholarly databases (ArXiv, PubMed, Semantic Scholar). | `search_paper`, `get_abstract` |
| **Regulatory** | `regulatory_server/` | Retrieves government regulations and legal documents. | `search_laws`, `get_regulation` |
| **Document** | `document_server/` | Heavy document processing (OCR, Layout Analysis) for uploaded files. | `parse_pdf`, `extract_tables` |
| **Qualitative** | `qualitative_server/` | Analysis of text data (Sentiment, Theme Extraction). | `analyze_sentiment`, `extract_themes` |

### 4. Utility Servers
System maintenance and advanced capabilities.

| Server Name | Directory | Description | Key Tools |
|:------------|:----------|:------------|:----------|
| **Browser Agent**| `browser_agent_server/`| Headless browser automation for complex JS-heavy sites (Playwright). | `browse_site`, `click_element` |
| **Crawler** | `crawler_server/` | Recursive spidering tools for sitemap exploration. | `crawl_domain`, `get_sitemap` |
| **Security** | `security_server/` | Scans URLs for safety and blocks malicious domains. | `scan_url`, `check_robots_txt` |
| **Tool Discovery**| `tool_discovery_server/`| Registry for dynamic tool capabilities (Service Registry). | `list_tools`, `get_tool_schema` |

## 🚀 Development

To add a new tool:
1.  Identify the correct server (or create a new one).
2.  Implement the tool function using `@mcp.tool`.
3.  The Orchestrator will automatically discover it on restart.

```bash
# Example: Run the Scraper Server independently
python -m mcp_servers.scraper_server.server
```
