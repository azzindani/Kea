# CLAUDE.md - AI Assistant Guidelines for Kea

This document provides essential context for AI assistants working with the Kea codebase.

## Project Overview

**Kea v4.0** is an Autonomous Enterprise Operating System - a "Generative ERP" that simulates a corporation where:
- **Employees** are AI agents (silicon workers)
- **Departments** are microservices
- **Workflows** are generated Just-In-Time as Directed Acyclic Graphs (DAGs)

The system evolved from DARE (Distributed Autonomous Research Engine) into an enterprise-grade platform capable of complex, non-linear problem solving.

## Quick Reference

```bash
# Install dependencies
uv sync

# Run a specific service
uv run python -m services.<service_name>.main

# Run all services locally
docker-compose up -d

# Database migrations
uv run alembic upgrade head

# Lint code
uv run ruff check .

# Type checking
uv run mypy .

# Run stress test (boots core servers automatically)
uv run pytest tests/stress/stress_test.py --query="Your query here" -v -s
```

## Architecture Overview

### The 7-Service Architecture ("Fractal Corp")

| Service | Port | Persona | Role |
|---------|------|---------|------|
| **API Gateway** | 8000 | The Mouth | Security, authentication, routing |
| **Orchestrator** | 8001 | The Brain | LangGraph reasoning engine, DAG execution |
| **MCP Host** | 8002 | The Hands | Tool execution, JIT server spawning |
| **RAG Service** | 8003 | The Librarian | Multi-source knowledge retrieval |
| **Vault** | 8004 | The Memory | Research persistence, artifact storage |
| **Swarm Manager** | 8005 | The Conscience | Governance, compliance, resource gating |
| **Chronos** | 8006 | The Clock | Scheduling, future task coordination |

### Key Architectural Patterns

1. **Split-Brain Design**: Reasoning (Orchestrator/LLM) is decoupled from Execution (MCP Host) to prevent hallucinations from bypassing guardrails
2. **Artifact Bus**: Vault-centric data flow where services are stateless and pull data via API
3. **JIT Spawning**: MCP servers are dynamically resolved and spawned on-demand with `uv`
4. **Hardware-Aware Adaptation**: Automatic resource detection adjusts worker counts and batch sizes
5. **Phased Fractal Spawning**: Complex tasks decomposed into parallel phases respecting DAG dependencies

## Directory Structure

```
Kea/
├── services/           # 7 microservices (Gateway, Orchestrator, MCP Host, RAG, Vault, Swarm Manager, Chronos)
├── shared/             # Shared library: schemas, config, messaging, hardware adapters, LLM/MCP abstractions
├── mcp_servers/        # 68+ MCP tool servers organized by domain (finance, data science, web3, etc.)
├── workers/            # Background job processors (research, shadow lab, synthesis)
├── configs/            # YAML configuration (prompts, settings, tool registry, monitoring)
├── migrations/         # Alembic database migrations
├── k8s/                # Kubernetes manifests
├── tests/              # Test suite (unit, integration, stress, simulation, e2e)
└── references/         # Reference documentation
```

## Code Conventions

### Naming
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `SCREAMING_SNAKE_CASE`

### Python Standards
- **Python version**: 3.11+
- **Package manager**: `uv` (preferred) or `pip`
- **Type hints**: Required on all functions
- **Async-first**: Use `async/await` for all I/O operations
- **Data validation**: Use Pydantic models for all data structures
- **Logging**: Use `structlog` with JSON output
- **Error handling**: Meaningful exception messages with proper context

### Code Style
- Line length: 100 characters (configured in ruff)
- Linting: `ruff` with rules E, F, I, N, W, UP
- Type checking: `mypy` in strict mode

## Key Files to Know

### Configuration
- `shared/config.py` - Centralized Pydantic-based configuration with `get_settings()`
- `configs/settings.yaml` - Service ports, API keys, JIT controls
- `configs/prompts.yaml` - Domain-specific LLM prompts
- `configs/tool_registry.yaml` - 68+ MCP server definitions
- `.env.example` - Environment variable template

### Core Schemas
- `shared/schemas.py` - Domain models: `ResearchState`, `AtomicFact`, `ToolOutput`, `Message`
- `shared/messaging.py` - Inter-agent async message bus
- `shared/dispatcher.py` - PostgreSQL-backed persistent task queue

### Service Entry Points
Each service has its entry point at `services/<service_name>/main.py`

## MCP Servers (68+ "Departments")

MCP servers provide specialized tool capabilities. Located in `/mcp_servers/`:

**Finance**: yfinance, yahooquery, finta, pandas_ta, mibian, ccxt, sec_edgar, finviz, tradingview, pdr
**Data Science**: pandas, numpy, duckdb, sklearn, statsmodels, scipy, xgboost, seaborn, matplotlib, plotly
**Web/Scraping**: playwright, browser_agent, crawler, newspaper, beautifulsoup4, ddg_search
**Documents**: pdfplumber, docx, openpyxl, zipfile, xmltodict
**Academic**: academic_server, document parsing, regulatory research
**Web3**: web3, security, blockchain analysis

Each MCP server follows this structure:
```
mcp_servers/<server_name>/
├── server.py           # FastMCP entry point
├── tools/              # Modularized tool implementations
├── pyproject.toml      # Dependencies (managed by uv)
└── README.md           # Tool documentation
```

## Environment Setup

Required environment variables (see `.env.example`):
```bash
OPENROUTER_API_KEY=sk-or-...      # LLM provider
DATABASE_URL=postgresql://...      # PostgreSQL with pgvector
REDIS_URL=redis://...              # Optional: Redis for caching
JWT_SECRET=...                     # API Gateway auth
```

## Database

- **PostgreSQL** with `pgvector` extension for vector embeddings
- **ORM**: SQLAlchemy with async support (`asyncpg`)
- **Migrations**: Alembic in `/migrations/versions/`
- Run migrations: `uv run alembic upgrade head`

## Testing

The project uses a pyramid testing strategy:

| Level | Location | Purpose |
|-------|----------|---------|
| Unit | `tests/unit/` | Fast, mocked tests |
| Integration | `tests/integration/` | Multi-service tests |
| MCP | `tests/mcp/` | Protocol compliance |
| Real LLM | `tests/real/` | Tests with actual LLM APIs |
| Stress | `tests/stress/` | Load testing (20+ concurrent jobs) |
| Simulation | `tests/simulation/` | Chaos/failure injection |
| E2E | `tests/e2e/` | Full pipeline integration |

Test markers (defined in `pytest.ini`):
- `@pytest.mark.unit`
- `@pytest.mark.integration`
- `@pytest.mark.mcp`
- `@pytest.mark.stress`
- `@pytest.mark.slow`
- `@pytest.mark.simulation`

## Common Development Tasks

### Adding a New MCP Server
1. Create directory in `mcp_servers/<server_name>/`
2. Add `server.py` with FastMCP setup
3. Create `tools/` directory with tool implementations
4. Add `pyproject.toml` with dependencies
5. Register in `configs/tool_registry.yaml`

### Adding a New Service Endpoint
1. Locate the appropriate service in `services/<service_name>/`
2. Add route handlers following existing patterns
3. Use Pydantic models for request/response validation
4. Add structured logging with `structlog`

### Modifying Shared Code
1. Changes in `shared/` affect all services
2. Ensure backward compatibility
3. Update type hints and docstrings
4. Run type checking: `uv run mypy shared/`

## Important Patterns

### Using the Settings System
```python
from shared.config import get_settings

settings = get_settings()
api_key = settings.openrouter_api_key
timeout = settings.timeouts.llm_completion
```

### Structured Logging
```python
import structlog

log = structlog.get_logger()
log.info("operation_completed", job_id=job_id, duration=elapsed)
```

### Async Database Operations
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_item(session: AsyncSession, item_id: str):
    result = await session.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()
```

### Pydantic Model Patterns
```python
from pydantic import BaseModel, Field

class ToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    timeout: float = 30.0
```

## Deployment

### Local Development
```bash
docker-compose up -d
```

### Production (Kubernetes)
Manifests in `/k8s/` directory with deployments, services, and config maps.

### Observability Stack
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Dashboards (port 3000)
- Alerts configured in `configs/alerting/alerts.yml`

## Troubleshooting

### Service Won't Start
1. Check PostgreSQL is running with pgvector extension
2. Verify `.env` file exists with required variables
3. Run `uv run alembic upgrade head` for migrations

### MCP Server Fails
1. Check server is registered in `tool_registry.yaml`
2. Verify dependencies in server's `pyproject.toml`
3. Check logs for JIT spawning errors

### LLM Calls Failing
1. Verify `OPENROUTER_API_KEY` is set
2. Check rate limits and quotas
3. Review timeout settings in `shared/config.py`

## Security Considerations

- Never hardcode secrets - use environment variables
- All external inputs must be validated via Pydantic
- Services communicate over internal network only
- API Gateway handles authentication and rate limiting
- Follow Zero-Trust model for service communication
