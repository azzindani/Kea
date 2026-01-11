# 🧪 Kea Research Engine Test Suite

Complete test suite with **17 MCP servers** and **87 tools**.

---

## 📊 Quick Summary

| Metric | Count |
|--------|:-----:|
| MCP Servers | 17 |
| Total Tools | 87 |
| Unit Tests | 35+ |
| Simulation Tests | 40+ |
| Workflow Tests | 5 |

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install pydantic httpx pandas numpy scikit-learn yfinance plotly beautifulsoup4 pytest pytest-asyncio

# Run standalone simulation (easiest - no pytest needed)
python tests/simulation/run_simulation.py

# Run unit tests (no API)
pytest tests/unit -v

# Run simulation tests
pytest tests/simulation -v
```

---

## 📁 Test Directory Structure

```
tests/
├── unit/                              # Unit tests (no API)
│   ├── test_schemas.py                # Schema validation
│   ├── test_config.py                 # Configuration
│   ├── test_mcp_protocol.py           # MCP protocol
│   ├── test_vector_store.py           # Vector storage
│   ├── test_graph_rag.py              # Graph RAG
│   ├── test_embedding.py              # Embeddings
│   ├── test_scraper_tools.py          # Scraper tools
│   ├── test_search_tools.py           # Search tools
│   ├── test_python_tools.py           # Python tools
│   ├── test_analysis_server.py        # Analysis server
│   ├── test_vision_tools.py           # Vision tools
│   ├── test_logging_detailed.py       # Logging
│   ├── test_new_servers.py            # Phase 1 servers
│   ├── test_phase2_servers.py         # Phase 2 servers
│   ├── test_phase3_servers.py         # Phase 3 servers
│   └── test_phase4_servers.py         # Phase 4 servers
│
├── simulation/                         # Real API simulation tests
│   ├── run_simulation.py              # Standalone runner (no pytest)
│   ├── test_new_servers_simulation.py # All server simulations
│   ├── test_workflow_simulation.py    # E2E workflows
│   └── test_research_simulation.py    # Research flows
│
├── integration/                        # API integration tests
│   └── test_e2e.py                    # End-to-end API tests
│
├── mcp/                               # MCP-specific tests
│   └── ...
│
├── stress/                            # Stress/load tests
│   └── ...
│
└── README.md                          # This file
```

---

## 📦 MCP Server Test Coverage

### Original Servers (5 servers, 14 tools)
| Server | Tools | Unit Test | Simulation |
|--------|:-----:|:---------:|:----------:|
| scraper_server | 3 | ✅ | ✅ |
| search_server | 3 | ✅ | ✅ |
| python_server | 3 | ✅ | ✅ |
| analysis_server | 2 | ✅ | ✅ |
| vision_server | 3 | ✅ | ✅ |

### Phase 1: Data & ML (6 servers, 29 tools)
| Server | Tools | Unit Test | Simulation |
|--------|:-----:|:---------:|:----------:|
| data_sources_server | 4 | ✅ | ✅ |
| analytics_server | 6 | ✅ | ✅ |
| crawler_server | 5 | ✅ | ✅ |
| ml_server | 5 | ✅ | ✅ |
| visualization_server | 4 | ✅ | ✅ |
| document_server | 5 | ✅ | ✅ |

### Phase 2: Research (3 servers, 18 tools)
| Server | Tools | Unit Test | Simulation |
|--------|:-----:|:---------:|:----------:|
| academic_server | 6 | ✅ | ✅ |
| regulatory_server | 6 | ✅ | ✅ |
| browser_agent_server | 6 | ✅ | ✅ |

### Phase 3: Qualitative/Security (2 servers, 16 tools)
| Server | Tools | Unit Test | Simulation |
|--------|:-----:|:---------:|:----------:|
| qualitative_server | 10 | ✅ | ✅ |
| security_server | 6 | ✅ | ✅ |

### Phase 4: Tool Discovery (1 server, 10 tools)
| Server | Tools | Unit Test | Simulation |
|--------|:-----:|:---------:|:----------:|
| tool_discovery_server | 10 | ✅ | ✅ |

---

## 🔬 Simulation Tests Detail

### `run_simulation.py` - Standalone Script
Run all simulations without pytest:
```bash
python tests/simulation/run_simulation.py
```

Tests included:
- CSV fetch with real data
- Yahoo Finance stock data
- EDA on diabetes dataset
- Correlation matrix
- ML clustering
- Anomaly detection
- arXiv paper search
- PubMed search
- Link extraction
- Source validation
- Entity extraction
- Fact triangulation
- URL scanning
- Content sanitization
- Code safety check
- PyPI search
- Package evaluation
- MCP stub generation

### `test_new_servers_simulation.py` - Pytest
```bash
pytest tests/simulation/test_new_servers_simulation.py -v
```

Classes:
- `TestDataSourcesSimulation` - CSV, yfinance
- `TestAnalyticsSimulation` - EDA, correlation, cleaning
- `TestMLSimulation` - AutoML, clustering, anomaly
- `TestCrawlerSimulation` - Links, sitemap
- `TestAcademicSimulation` - arXiv, PubMed, Semantic Scholar
- `TestRegulatorySimulation` - Federal Register, EDGAR
- `TestBrowserAgentSimulation` - Validation, search
- `TestQualitativeSimulation` - Entities, triangulation, graph
- `TestSecuritySimulation` - URL scan, sanitize, code check
- `TestToolDiscoverySimulation` - PyPI, evaluate, stub

### `test_workflow_simulation.py` - E2E Workflows
```bash
pytest tests/simulation/test_workflow_simulation.py -v
```

Workflows:
1. **Financial Research** - Stock data → EDA → Academic papers
2. **Medical Research** - PubMed → Dataset → ML model
3. **Investigative Research** - Entity extraction → Graph → Triangulation
4. **Tool Discovery** - Search → Evaluate → Generate stub
5. **Data Pipeline** - Fetch → Clean → Analyze → Model

---

## 🧪 Sample Data URLs

```python
SAMPLE_URLS = {
    "adidas": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
    "diabetes": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
    "churn": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Ecommerce_Customer_Churn.csv",
    "bike_sales": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Europe_Bike_Sales.csv",
    "property": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/NYC_Property_Sales.csv",
    "loan": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Loan_Default.csv",
}
```

---

## ✅ Run Commands

| Purpose | Command |
|:--------|:--------|
| Standalone simulation | `python tests/simulation/run_simulation.py` |
| Quick unit tests | `pytest tests/unit -v -x` |
| All simulations | `pytest tests/simulation -v` |
| Specific server | `pytest tests/simulation -k "academic" -v` |
| Full suite | `pytest tests -v --tb=short` |
| With coverage | `pytest tests --cov=mcp_servers --cov=shared` |
| Workflows only | `pytest tests/simulation/test_workflow_simulation.py -v` |

---

## 📋 Dependencies

```bash
# Core
pip install pydantic httpx pandas numpy

# ML
pip install scikit-learn

# Data Sources
pip install yfinance

# Visualization
pip install plotly matplotlib seaborn

# Document Parsing
pip install beautifulsoup4 pymupdf python-docx openpyxl

# Testing
pip install pytest pytest-asyncio
```

---

## 🔧 Tool Categories Tested

| Category | Tools | Sample Tests |
|----------|:-----:|--------------|
| Data Collection | 15 | CSV fetch, yfinance, FRED |
| Analytics/ML | 17 | EDA, AutoML, clustering |
| Documents | 10 | PDF, DOCX, HTML parsing |
| Browsing | 6 | Source validation, search |
| Qualitative | 10 | Entity extraction, graph |
| Security | 6 | URL scan, code safety |
| Discovery | 10 | PyPI search, stub gen |
