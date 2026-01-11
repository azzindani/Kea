# 🧪 Kea Research Engine - Test Suite

Complete test documentation for running all tests.

---

## � Quick Start

### Prerequisites

```bash
# Install all dependencies
pip install pydantic httpx pandas numpy scikit-learn yfinance plotly matplotlib seaborn beautifulsoup4 pymupdf python-docx openpyxl pytest pytest-asyncio pytest-timeout
```

### Run All Tests

```bash
# Navigate to project root
cd d:\Antigravity\Kea

# Run everything
pytest tests -v
```

---

## 📋 Test Categories

| Category | Path | Description | Requires API |
|----------|------|-------------|:------------:|
| Unit | `tests/unit/` | Core functionality tests | ❌ |
| Simulation | `tests/simulation/` | Real API calls | ✅ Internet |
| Integration | `tests/integration/` | Full API endpoints | ✅ API Server |
| MCP | `tests/mcp/` | MCP protocol tests | ❌ |
| Stress | `tests/stress/` | Load testing | ✅ API Server |

---

## � How to Run Each Test Type

### 1. Unit Tests (No API Required)

```bash
# Run all unit tests
pytest tests/unit -v

# Run with short traceback
pytest tests/unit -v --tb=short

# Stop on first failure
pytest tests/unit -v -x

# Run specific test file
pytest tests/unit/test_schemas.py -v

# Run specific test class
pytest tests/unit/test_new_servers.py::TestDataSourcesServer -v

# Run specific test function
pytest tests/unit/test_new_servers.py::TestDataSourcesServer::test_init -v
```

**Unit test files:**
- `test_schemas.py` - Schema validation
- `test_config.py` - Configuration
- `test_mcp_protocol.py` - MCP protocol
- `test_vector_store.py` - Vector storage
- `test_graph_rag.py` - Graph RAG
- `test_embedding.py` - Embeddings
- `test_scraper_tools.py` - Scraper tools
- `test_search_tools.py` - Search tools
- `test_python_tools.py` - Python tools
- `test_analysis_server.py` - Analysis server
- `test_vision_tools.py` - Vision tools
- `test_logging_detailed.py` - Logging
- `test_new_servers.py` - Phase 1 servers
- `test_phase2_servers.py` - Phase 2 servers
- `test_phase3_servers.py` - Phase 3 servers
- `test_phase4_servers.py` - Phase 4 servers

---

### 2. Simulation Tests (Requires Internet)

These tests make real API calls to external services (arXiv, PubMed, PyPI, etc.)

```bash
# OPTION A: Standalone script (EASIEST - no pytest needed)
python tests/simulation/run_simulation.py

# OPTION B: Run all simulation tests with pytest
pytest tests/simulation -v

# Run specific simulation file
pytest tests/simulation/test_new_servers_simulation.py -v

# Run workflow tests only
pytest tests/simulation/test_workflow_simulation.py -v

# Run tests for specific server
pytest tests/simulation/test_new_servers_simulation.py -k "academic" -v
pytest tests/simulation/test_new_servers_simulation.py -k "security" -v
pytest tests/simulation/test_new_servers_simulation.py -k "ml" -v
```

**Simulation test files:**
- `run_simulation.py` - Standalone runner (no pytest)
- `test_new_servers_simulation.py` - All 12 new servers
- `test_workflow_simulation.py` - End-to-end workflows
- `test_research_simulation.py` - Research flow tests

---

### 3. Integration Tests (Requires API Server)

```bash
# Terminal 1: Start API server
python -m services.api_gateway.main

# Terminal 2: Run integration tests
pytest tests/integration -v
```

---

### 4. Run by Server/Feature

```bash
# Data sources
pytest tests -k "data_sources" -v

# Analytics
pytest tests -k "analytics" -v

# ML
pytest tests -k "ml" -v

# Academic sources
pytest tests -k "academic" -v

# Security
pytest tests -k "security" -v

# Qualitative analysis
pytest tests -k "qualitative" -v

# Tool discovery
pytest tests -k "tool_discovery" -v
```

---

## 📊 Complete Test Commands

| What to Test | Command |
|:-------------|:--------|
| **Everything** | `pytest tests -v` |
| **Unit only** | `pytest tests/unit -v` |
| **Simulations only** | `pytest tests/simulation -v` |
| **Standalone simulation** | `python tests/simulation/run_simulation.py` |
| **Quick check** | `pytest tests/unit -v -x` |
| **With coverage** | `pytest tests --cov=mcp_servers --cov=shared` |
| **Verbose output** | `pytest tests -v --tb=long` |
| **Show print output** | `pytest tests -v -s` |

---

## 📁 Directory Structure

```
tests/
├── unit/                              # Unit tests (offline)
│   ├── test_schemas.py
│   ├── test_config.py
│   ├── test_mcp_protocol.py
│   ├── test_vector_store.py
│   ├── test_graph_rag.py
│   ├── test_embedding.py
│   ├── test_scraper_tools.py
│   ├── test_search_tools.py
│   ├── test_python_tools.py
│   ├── test_analysis_server.py
│   ├── test_vision_tools.py
│   ├── test_logging_detailed.py
│   ├── test_new_servers.py           # Phase 1
│   ├── test_phase2_servers.py        # Phase 2
│   ├── test_phase3_servers.py        # Phase 3
│   └── test_phase4_servers.py        # Phase 4
│
├── simulation/                        # Real API tests
│   ├── run_simulation.py             # Standalone (no pytest)
│   ├── test_new_servers_simulation.py
│   ├── test_workflow_simulation.py
│   └── test_research_simulation.py
│
├── integration/                       # API integration
│   └── test_e2e.py
│
├── mcp/                              # MCP protocol
│   └── ...
│
├── stress/                           # Load testing
│   └── ...
│
└── README.md                         # This file
```

---

## 🧪 Sample Data URLs

The simulation tests use these real CSV files:

```python
SAMPLE_URLS = {
    "adidas_sales": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
    "diabetes": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
    "churn": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Ecommerce_Customer_Churn.csv",
    "bike_sales": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Europe_Bike_Sales.csv",
}
```

---

## 📦 MCP Servers Tested

| Phase | Server | Tools | Test File |
|:------|:-------|:-----:|:----------|
| Original | scraper_server | 3 | test_scraper_tools.py |
| Original | search_server | 3 | test_search_tools.py |
| Original | python_server | 3 | test_python_tools.py |
| Original | analysis_server | 2 | test_analysis_server.py |
| Original | vision_server | 3 | test_vision_tools.py |
| Phase 1 | data_sources_server | 4 | test_new_servers.py |
| Phase 1 | analytics_server | 6 | test_new_servers.py |
| Phase 1 | crawler_server | 5 | test_new_servers.py |
| Phase 1 | ml_server | 5 | test_new_servers.py |
| Phase 1 | visualization_server | 4 | test_new_servers.py |
| Phase 1 | document_server | 5 | test_new_servers.py |
| Phase 2 | academic_server | 6 | test_phase2_servers.py |
| Phase 2 | regulatory_server | 6 | test_phase2_servers.py |
| Phase 2 | browser_agent_server | 6 | test_phase2_servers.py |
| Phase 3 | qualitative_server | 10 | test_phase3_servers.py |
| Phase 3 | security_server | 6 | test_phase3_servers.py |
| Phase 4 | tool_discovery_server | 10 | test_phase4_servers.py |

**Total: 17 servers, 87 tools**

---

## ⚠️ Troubleshooting

### Missing module error
```bash
pip install <module_name>
```

### pytest not found
```bash
pip install pytest pytest-asyncio
```

### Import errors
```bash
# Run from project root
cd d:\Antigravity\Kea
python -m pytest tests -v
```

### Timeout on simulation tests
Some API calls may be slow. Increase timeout:
```bash
pytest tests/simulation -v --timeout=120
```
