# 🔌 MCP Servers ("The Hands")

This directory contains the **Model Context Protocol (MCP)** compliant microservices. These are the "Hands" of the AI system, providing the capabilities required to interact with the external world, execute code, and perform complex data analysis.

---

## 🏗️ Architecture Overview

Kea implements a **Hub-and-Spoke** architecture where the **MCP Host** acts as the universal client and process manager for a fleet of specialized tool servers.

```mermaid
graph TD
    Host[MCP Host Service]
    
    subgraph Tool Layer [Isolated MCP Servers]
        Scraper[Scraper Server]
        Python[Python Sandbox]
        Search[Search Server]
        Vision[Vision Server]
        Analytics[Analytics Server]
    end
    
    Host -->|JSON-RPC via Stdio| Scraper
    Host -->|JSON-RPC via Stdio| Python
    Host -->|JSON-RPC via Stdio| Search
    
    Scraper -.->|ToolResult| Host
    Python -.->|ToolResult| Host
```

1.  **Fault Isolation**: Each server runs in a separate OS process. A crash in the `scraper` does not affect the `python` sandbox.
2.  **Stateless Execution**: Servers are largely stateless, receiving all necessary context in the JSON-RPC request.
3.  **Unified Interface**: All 32 servers follow the same MCP handshake and tool discovery protocol.

---

## 🧩 Server Catalog & Reference

We categorize servers by their cognitive domain.

### 1. Core Execution & Retrieval
| Server | Directory | Description |
|:-------|:----------|:------------|
| **Scraper** | `scraper_server/` | Stealthy browsing and document extraction. |
| **Search** | `search_server/` | Global information discovery via Tavily/Brave. |
| **Python** | `python_server/` | Sandboxed computation and DB interaction. |
| **Vision** | `vision_server/` | Multimodal analysis of screenshots and plots. |
| **Crawler** | `crawler_server/` | Targeted site crawling and indexing. |
| **Browser** | `browser_agent_server/`| Specialized browser automation agent. |
| **Newspaper** | `newspaper_server/` | Structured news article/metadata extraction. |
| **Document** | `document_server/` | PDF and structured document parsing. |
| **Filesystem**| `filesystem_server/` | Isolated local file management. |
| **Analysis** | `analysis_server/` | Meta-analysis and trend detection. |
| **Analytics** | `analytics_server/` | Exploratory Data Analysis (EDA) and profiling. |

### 2. Quant & Market Analytics
| Server | Directory | Description |
|:-------|:----------|:------------|
| **TradingView**| `tradingview_server/` | Consensus TA and market screening. |
| **CCXT** | `ccxt_server/` | Unified crypto exchange data and trading. |
| **Finta** | `finta_server/` | Financial Technical Analysis indicators. |
| **Pandas TA** | `pandas_ta_server/` | High-perf TA for dataframe pipelines. |
| **Mibian** | `mibian_server/` | Advanced options pricing models. |
| **Finviz** | `finviz_server/` | Visual stock screening and heatmaps. |
| **ML** | `ml_server/` | Machine learning training and inference. |
| **Vis** | `visualization_server/`| Interactive Plotly/Table visualization. |

### 3. Global Data & Economies
| Server | Directory | Description |
|:-------|:----------|:------------|
| **WBGAPI** | `wbgapi_server/` | World Bank global development indicators. |
| **YahooQuery** | `yahooquery_server/` | High-speed Yahoo Finance bulk retrieval. |
| **yFinance** | `yfinance_server/` | Deep historical and fundamental data. |
| **PDR** | `pdr_server/` | Remote data retrieval (Fred, Stlouis, etc). |
| **SEC Edgar** | `sec_edgar_server/` | Bulk SEC filing downloads and parsing. |
| **Py Edgar** | `python_edgar_server/` | Metadata-focused SEC research. |
| **Data Src** | `data_sources_server/`| Unified external API gateway. |

### 4. Knowledge, Logic & Web3
| Server | Directory | Description |
|:-------|:----------|:------------|
| **Qualitative**| `qualitative_server/` | Forensics, mapping and thematic NLP. |
| **Web3** | `web3_server/` | Blockchain RPC, DeFi, and Smart Contracts. |
| **Regulatory**| `regulatory_server/` | Compliance tracking and legal research. |
| **Academic** | `academic_server/` | ArXiv and Semantic Scholar search. |
| **Security** | `security_server/` | URL scanning and code safety auditing. |
| **Discovery** | `tool_discovery_server/`| Self-expansion and tool stub generation. |

---

## 🔬 Deep Dive: The MCP Handshake

The communication between the **MCP Host** and its **Servers** follows the JSON-RPC 2.0 standard.

### 1. The Startup Sequence
1.  **Spawn**: Host spawns the server process (e.g., `uv run python -m mcp_servers.scraper_server.server`).
2.  **Initialize**: Host sends `initialize` request with client capabilities.
3.  **Capabilities**: Server responds with its name, version, and supported features (e.g., `listChanged`, `subscribe`).
4.  **Discovery**: Host calls `tools/list` to retrieve the JSON schemas for every tool the server provides.

### 2. JIT Dependency Resolution
Kea's MCP servers are designed to be "Zero-Config." They define their own dependencies in their `main.py` entrypoint. The **JIT Loader** in the shared library parses these requirements and ensures they are installed in the ephemeral `uv` environment before the server enters the ready state.

---

## 🛠️ Development Reference

### Adding a New Tool
To extend the capabilities of an existing server:

1.  **Define**: Add a function in the server's `tools.py` or `server.py`.
2.  **Decorate**: Use the `@mcp.tool()` decorator to expose it.
3.  **Document**: Provide a clear docstring and type hints; these are used to generate the JSON Schema for the LLM.

```python
@mcp.tool()
async def analyze_sentiment(text: str) -> str:
    """
    Analyze the emotional tone of a text block.
    
    Args:
        text: The raw string to analyze.
    """
    # Logic goes here...
    return "Positive"
```

### Standard Response Format
All tools must return an `MCPResult` (or `ToolResult`), which consists of:
- `content`: A list of `TextContent` or `ImageContent` objects.
- `isError`: A boolean flag indicating functional failure.
