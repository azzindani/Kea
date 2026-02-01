# 🔌 MCP Servers ("The Hands")

The `mcp_servers/` directory contains the **Model Context Protocol (MCP)** compliant microservices. These are the "Hands" of the Kea system, providing the specialized capabilities required to interact with the external world, execute code, and perform deep domain-specific analysis.

## ✨ Features

- **Massive Tool Library**: 68+ specialized servers covering Finance, Web3, Academic Research, GIS, and Data Science.
- **Hub-and-Spoke Architecture**: Centrally managed by the `MCP Host`, with each server running in an isolated, low-privilege process.
- **JIT Dependency Resolution**: Servers use `uv` and `FastMCP` to dynamically resolve and install their own dependencies at runtime.
- **n8n-Style Data Chaining**: Tools are designed to produce structured outputs that can be piped into subsequent tools without LLM intervention.
- **Stealth Browsing & Extraction**: High-fidelity scraping via Playwright with built-in anti-bot evasion and automatic markdown conversion.
- **Zero-Trust Tooling**: Every tool execution is logged, audited, and resource-gated by the Swarm Manager.

---

## 📐 Architecture

Kea treats tools as isolated micro-agents rather than simple function calls.

### 🗼 The Tool Ecosystem

```mermaid
graph TD
    Host[MCP Host Service]
    
    subgraph "Core Servers"
        Scraper[Scraper/Browser]
        Python[Python Sandbox]
        Search[Global Search]
    end
    
    subgraph "Domain Servers"
        Quant[Quant/Finance]
        Academic[arXiv/Scholar]
        Web3[Blockchain RPC]
    end
    
    Host -->|JSON-RPC| Core
    Host -->|JSON-RPC| Domain
    
    Core -->|Structured Data| Vault[(Vault)]
    Domain -->|Atomic Facts| Vault
```

---

## 📁 Codebase Structure

Each server (e.g., `yfinance_server/`) typically follows this structure:

- **`server.py`**: The main entrypoint using `FastMCP` to register tools.
- **`tools/`**: Modularized tool implementations (Market, Financials, etc.).
- **`Dockerfile`**: (Optional) For running the server in a containerized sandbox.
- **`README.md`**: Domain-specific documentation and tool references.

---

## 🧠 Deep Dive

### 1. JIT "Zero-Config" Spawning
Unlike traditional tool systems that require complex environment setups, Kea servers are self-contained. When the MCP Host needs the `yfinance_server`, it uses the `shared/tools/jit_loader` to parse the `dependencies` list in `server.py` and spawns a `uv` process that ensures the exact versions of `pandas`, `yfinance`, and `matplotlib` are present.

### 2. High-Fidelity Scraping (`playwright_server`)
The `playwright_server` is one of the most complex "Hands." It exposes 20+ tools for navigation, input, and extraction. It supports "Session Persistence," allowing an agent to log into a portal in one turn and continue browsing in the next without losing state.

### 3. Financial Intelligence Suite
Kea includes a multi-layered financial stack:
- **`yfinance` / `yahooquery`**: Fundamental data and history.
- **`finta` / `pandas_ta`**: Technical indicators (RSI, MACD, etc.).
- **`mibian`**: Black-Scholes and options Greeks.
- **`sec_edgar`**: Direct access to corporate filings for regulatory research.

---

## 📚 Reference

### Server Categories

| Category | Primary Servers | Capabilities |
|:---------|:----------------|:-------------|
| **Core** | `search`, `scraper`, `python` | Web search, stealth browsing, code execution. |
| **Quant** | `ccxt`, `yfinance`, `finta` | Crypto, stocks, technical analysis. |
| **Academic**| `academic`, `document` | arXiv, Semantic Scholar, PDF parsing. |
| **Analysis**| `pandas`, `sklearn`, `statsmodels`| ML, statistical modeling, data cleaning. |
| **Web3** | `web3`, `security` | Smart contracts, on-chain data, safety. |

### Tool Development Pattern

```python
@mcp.tool()
async def my_new_tool(query: str) -> str:
    """
    Clear docstring for the LLM to understand utility.
    """
    # implementation logic
    return "Result"
```

---

## 🛡️ MCP Server Standards

To ensure compatibility and stability across the ecosystem, all new servers must adhere to the following standards:

### 1. File Structure
```text
server_name/
├── pyproject.toml       # Managed by uv, defines dependencies
├── README.md            # Tool documentation
├── server.py            # Entry point, FastMCP initialization
└── tools/               # Tool implementations
    ├── __init__.py      # Exposes tools
    ├── core.py          # Shared logic/utilities
    └── feature_xxx.py   # Specialized tool functions
```

### 2. Implementation Rules
- **Framework**: Use `mcp.server.fastmcp.FastMCP`.
- **Async**: All tools must be `async def`.
- **Return Types**: Return `str` (typically JSON strings for data, plain text for logs). Use `to_serializable()` helpers for complex objects (SafeNum, etc.).
- **Dependencies**: 
  - Must be explicitly defined in `pyproject.toml`.
  - Use `uv` for management.
  - Pin versions if breaking changes are known (e.g., `pandas<2.0`).
- **Error Handling**: 
  - Wrap external API calls in `try/except`.
  - Log errors via `structlog`.
  - Return informative error strings to the LLM, don't crash the server.

### 3. Tool Design Philosophy
- **"Super Tools"**: Prefer comprehensive tools (e.g., `analyze_stock_full`) over granular ones (`get_price`, `get_volue`).
- **Bulk Operations**: Always implement bulk retrieval (e.g., `get_prices(symbols: List[str])`) to minimize round-trips.
- **Self-Contained**: Tools should manage their own state or be stateless.

---

## 🤖 Agent Protocol: Creating New Servers

When creating a new MCP server for a Python library (e.g., `{library_name}`), use the following protocol to ensure high-quality, high-utility integration.

### Phase 1: Research & Discovery
1.  **Documentation Deep Dive**: Read the official `{library_name}` docs. Understand its core objects, key methods, and unique capabilities.
2.  **Feature Mapping**: Identify distinct features (e.g., "Data Retrieval", "Analysis", "Plotting").
3.  **Tool Brainstorming**: List potential tools. Aim for 50-200 tools if the library is extensive.

### Phase 2: Implementation Plan
Create a plan that prioritizes:
1.  **Bulk Data Retrieval**: Can we get 100 items in one call?
2.  **"Super Functions"**: Can we combine `fetch`, `clean`, and `analyze` into one tool?
3.  **Multitalent Tools**: A single entry point for complex operations (e.g., `universal_converter`).

### Phase 3: Development
1.  **Scaffold**: Create the directory structure and `pyproject.toml`.
2.  **Core Logic**: Implement `tools/core.py` for shared resources (API clients, formatting).
3.  **Tool Implementation**: Group tools logically into files (e.g., `tools/market.py`, `tools/technical.py`).
4.  **Logging**: Integrate `structlog` for observability.
5.  **No Dummy Data**: All tools must interact with real library functions. Requires valid inputs/API keys if applicable.

### Phase 4: Verification
1.  **Dependency Check**: Run `uv sync`.
2.  **Connectivity Test**: Run `pytest tests/mcp/test_server_connectivity.py` to ensure the server works within the Kea ecosystem.

---

### 📝 Prompt Template for Agents

Use this prompt to instruct an agent to build a new server:

> **Objective**: Create an MCP Server for the `{Target Library}` Python library.
>
> **Requirements**:
> 1.  **Research**: Find and read all online documentation for `{Target Library}`. Understand every feature.
> 2.  **Plan**: Design a suite of tools (aim for maximum coverage, 50-200+ tools).
>     - **Prioritize Bulk**: Tools must handle lists of inputs (batch processing).
>     - **Create Super-Tools**: Combine atomic functions into high-value workflows (e.g., "Full Report").
> 3.  **Implement**:
>     - Use the standard `mcp_servers/` directory structure.
>     - Use `FastMCP` and `uv` for dependencies.
>     - Use `structlog` for logging.
>     - **NO DUMMY DATA**: Real library calls only.
> 4.  **Refine**:
>     - Update `mcp_servers/README.md` with the new server details.
>     - Ensure code is robust (try/except blocks).
