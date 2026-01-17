# Kea Test Suite

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/unit/ -v
pytest tests/real/ -v
pytest tests/integration/ -v
```

## Test Categories

| Category | Command | Description |
|----------|---------|-------------|
| **Unit** | `pytest tests/unit/` | Fast, mocked tests (~800 tests) |
| **Real LLM** | `pytest tests/real/` | Tests with actual LLM API calls |
| **Integration** | `pytest tests/integration/` | End-to-end pipeline tests |
| **E2E** | `pytest tests/e2e/` | Full user journey tests |
| **Simulation** | `pytest tests/simulation/` | Load & failure testing |
| **MCP** | `pytest tests/mcp/` | MCP server tests |
| **Verification** | `pytest tests/verification/` | Production readiness checks |

## Run Multiple Categories

```bash
# Run unit + real tests together
pytest tests/unit/ tests/real/ -v

# Run everything except simulation (slow)
pytest tests/ --ignore=tests/simulation/ -v
```

## Common Flags

| Flag | Meaning |
|------|---------|
| `-v` | Verbose - show test names |
| `-s` | Show print() output |
| `-q` | Quiet - just summary |
| `-x` | Stop on first failure |
| `--tb=short` | Shorter tracebacks |
| `-k "keyword"` | Run tests matching keyword |
| `--log-cli-level=INFO` | Show logger output |

## Debug & Advanced Options

```bash
# Stop on first failure with full traceback
pytest tests/ -x --tb=long

# Run with coverage report
pytest tests/unit/ --cov=shared --cov=services --cov-report=html

# Run with timeout (prevent hanging tests)
pytest tests/ --timeout=60

# Run tests in parallel (faster)
pytest tests/unit/ -n auto

# Show slowest 10 tests
pytest tests/ --durations=10

# Debug with pdb on failure
pytest tests/ --pdb

# Run only failed tests from last run
pytest tests/ --lf

# Run tests matching pattern
pytest tests/ -k "auth and not slow"

# Verbose logging with timestamps
pytest tests/ -v -s --log-cli-level=DEBUG --log-cli-format="%(asctime)s %(levelname)s %(message)s"
```

## Jupyter Notebook Setup (Kaggle/Colab)

### 1. Install Dependencies

```python
%%capture
!pip install pytest pytest-asyncio pytest-timeout pytest-cov aiohttp asyncpg
!pip install pydantic httpx pandas numpy sentence-transformers pydantic-settings
!pip install scikit-learn yfinance plotly matplotlib seaborn
!pip install beautifulsoup4 pymupdf python-docx openpyxl
!pip install langgraph langchain langchain-core
!pip install prometheus-client PyYAML qdrant-client
```

### 2. Setup PostgreSQL & Qdrant

```python
# Install and start PostgreSQL
!apt-get update && apt-get install -y postgresql postgresql-contrib
!service postgresql start

# Create database
!sudo -u postgres psql -c "CREATE USER kea WITH PASSWORD 'kea123';"
!sudo -u postgres psql -c "CREATE DATABASE kea OWNER kea;"
!sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kea TO kea;"

# Download and start Qdrant
!wget https://github.com/qdrant/qdrant/releases/download/v1.16.3/qdrant-x86_64-unknown-linux-gnu.tar.gz
!tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
```

### 3. Clone Repository & Set Environment

```python
!git clone -b antigravity https://github.com/azzindani/Kea.git
%cd /kaggle/working/Kea

import os, subprocess, time

# Start Qdrant in background
subprocess.Popen(["/kaggle/working/qdrant"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

# Set environment variables
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-YOUR_KEY_HERE"
os.environ["DATABASE_URL"] = "postgresql://kea:kea123@localhost:5432/kea"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["QDRANT_URL"] = "http://localhost:6333"
```

### 4. Start Services

```python
import threading, uvicorn, time

def start_api_gateway():
    from services.api_gateway.main import app
    uvicorn.run(app, host="127.0.0.1", port=8080)

def start_orchestrator():
    from services.orchestrator.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000)

def start_rag_service():
    from services.rag_service.main import app
    uvicorn.run(app, host="127.0.0.1", port=8001)

threading.Thread(target=start_api_gateway, daemon=True).start()
threading.Thread(target=start_orchestrator, daemon=True).start()
threading.Thread(target=start_rag_service, daemon=True).start()
time.sleep(30)  # Wait for services to start
```

### 5. Run Tests

```python
# Run unit tests
!python -m pytest tests/unit/ -v -q

# Run real LLM tests
!python -m pytest tests/real/ -v -s --log-cli-level=INFO

# Run all tests
!python -m pytest tests/ -v
```

## Environment Variables

### Required for Real LLM Tests

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | API key for OpenRouter LLM calls | `sk-or-v1-xxx...` |

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Falls back to SQLite |
| `REDIS_URL` | Redis connection for caching | In-memory fallback |
| `QDRANT_URL` | Qdrant vector database URL | `http://localhost:6333` |

### Service Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | API Gateway port | `8080` |
| `ORCHESTRATOR_PORT` | Orchestrator service port | `8000` |
| `RAG_SERVICE_PORT` | RAG service port | `8001` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT tokens | Auto-generated |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `60` |

### HuggingFace Sync (Optional)

| Variable | Description | Example |
|----------|-------------|---------|
| `HF_REPO_ID` | HuggingFace repository ID | `username/repo` |
| `HF_TOKEN` | HuggingFace API token | `hf_xxx...` |

### Hardware & Performance

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_WORKERS` | Maximum worker threads | Auto-detected |
| `BATCH_SIZE` | Processing batch size | Auto-detected |
| `EMBEDDING_DEVICE` | Device for embeddings | `cpu` or `cuda` |
| `RERANKER_DEVICE` | Device for reranker | `cpu` or `cuda` |

### Example: Full Environment Setup

```bash
# Required
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Database (optional - falls back to SQLite)
export DATABASE_URL="postgresql://kea:kea123@localhost:5432/kea"
export REDIS_URL="redis://localhost:6379"
export QDRANT_URL="http://localhost:6333"

# Service config
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"

# Authentication
export JWT_SECRET="your-secret-key-here"
```
