# 🧪 Kea Research Engine - Test Suite

Complete test documentation for running all tests.

---

## ⚠️ IMPORTANT: Test Categories

| Test Type | Command | Requires |
|:----------|:--------|:---------|
| **Unit (config only)** | `pytest tests/unit/test_config.py -v` | Nothing |
| **Unit (all)** | `pytest tests/unit -v` | All dependencies |
| **Simulation** | `pytest tests/simulation -v` | Internet + dependencies |
| **Integration** | `pytest tests/integration -v` | API server running |

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Core dependencies
pip install pydantic httpx pandas numpy

# Additional for full testing
pip install scikit-learn yfinance plotly matplotlib seaborn
pip install beautifulsoup4 pymupdf python-docx openpyxl
pip install pytest pytest-asyncio pytest-timeout
```

### Step 2: Choose What to Run

```bash
# ✅ SAFEST - Just config tests (no external deps)
pytest tests/unit/test_config.py tests/unit/test_mcp_protocol.py -v

# ✅ Unit tests only (no API, no internet)
pytest tests/unit -v

# ✅ Simulation with internet (no API server needed)
pytest tests/simulation -v

# ❌ Integration tests (REQUIRES API SERVER RUNNING FIRST)
# Terminal 1: python -m services.api_gateway.main
# Terminal 2: pytest tests/integration -v
```

---

## 📋 Run by Environment

### For Colab/Kaggle (Limited Internet)

```bash
# Install minimal deps
pip install pydantic pytest pytest-asyncio

# Run only config and schema tests
pytest tests/unit/test_config.py tests/unit/test_schemas.py -v
```

### For Local Development (Full Setup)

```bash
# Install all deps
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit -v

# Run simulation tests (needs internet)
pytest tests/simulation -v
```

### For Full Testing (API Required)

```bash
# Terminal 1: Start API
python -m services.api_gateway.main

# Terminal 2: Run all tests
pytest tests -v
```

---

## 🔧 Run Specific Test Types

```bash
# Config tests only (always works)
pytest tests/unit/test_config.py -v

# MCP protocol tests (always works)
pytest tests/unit/test_mcp_protocol.py -v

# Schema tests
pytest tests/unit/test_schemas.py -v

# Skip integration tests
pytest tests --ignore=tests/integration --ignore=tests/stress -v

# Skip failing tests and continue
pytest tests -v --ignore=tests/integration -x

# Run only tests that passed before
pytest tests/unit/test_config.py tests/unit/test_mcp_protocol.py -v
```

---

## 📊 Test Results Summary

Based on your run, these tests **PASSED**:

| Test | Status |
|:-----|:------:|
| `test_config.py::test_get_settings` | ✅ |
| `test_config.py::test_settings_singleton` | ✅ |
| `test_config.py::test_environment_enum` | ✅ |
| `test_config.py::test_llm_config` | ✅ |
| `test_config.py::test_mcp_config` | ✅ |
| `test_config.py::test_api_key_from_env` | ✅ |
| `test_mcp_protocol.py::TestJSONRPCRequest` | ✅ |
| `test_mcp_protocol.py::TestJSONRPCResponse` | ✅ |
| `test_mcp_protocol.py::TestTool` | ✅ |
| `test_mcp_protocol.py::TestToolResult` | ✅ |
| `test_schemas.py::test_create_full` | ✅ |
| `test_schemas.py::test_create_source` | ✅ |
| `test_schemas.py::test_job_types` | ✅ |
| `test_schemas.py::test_create_research_state` | ✅ |
| `test_schemas.py::test_research_status_progression` | ✅ |
| `test_research_simulation.py::test_consensus_simulation` | ✅ |

---

## ❌ Why Tests Fail

| Failure Type | Cause | Solution |
|:-------------|:------|:---------|
| `ConnectError` | API server not running | Start API first |
| `ModuleNotFoundError` | Missing dependency | `pip install <module>` |
| `ImportError` | Package not installed | Install dependencies |
| `httpcore.ConnectError` | No internet or API | Run locally with internet |

---

## 📁 Directory Structure

```
tests/
├── unit/                    # Offline tests
│   ├── test_config.py       # ✅ Always works
│   ├── test_mcp_protocol.py # ✅ Always works  
│   ├── test_schemas.py      # ✅ Mostly works
│   └── ...                  # Need dependencies
│
├── simulation/              # Need internet
│   ├── run_simulation.py    # Standalone script
│   └── ...
│
├── integration/             # Need API server
│   └── ...
│
└── README.md
```

---

## 🎯 Recommended Commands

```bash
# 1. Quick check (always works)
pytest tests/unit/test_config.py -v

# 2. More tests (needs pydantic)
pytest tests/unit/test_config.py tests/unit/test_schemas.py tests/unit/test_mcp_protocol.py -v

# 3. All unit tests (needs all deps)
pytest tests/unit -v --ignore=tests/integration

# 4. Standalone simulation (no pytest)
python tests/simulation/run_simulation.py
```
