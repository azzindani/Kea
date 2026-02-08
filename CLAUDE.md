# CLAUDE.md - Kea Development Guide

## Project Overview

Kea v4.0 is an Autonomous Enterprise Operating System — a Generative ERP that simulates a
100,000+ employee corporation where AI agents ("employees") operate across microservices
("departments") executing Just-In-Time DAG workflows. The project name is `research-engine`,
licensed MIT, written in Python 3.11+.

## Architecture

Seven microservices with distinct roles, communicating via REST APIs (zero shared filesystem):

| Service | Port | Role |
|---------|------|------|
| API Gateway | 8000 | Auth, routing, REST entry point |
| Orchestrator | 8001 | LangGraph state machine & reasoning engine |
| MCP Host | 8002 | Tool execution & JIT server spawning |
| RAG Service | 8003 | Multi-source knowledge retrieval |
| Vault | 8004 | Research persistence & context engine |
| Swarm Manager | 8005 | Governance, compliance, resource gating |
| Chronos | 8006 | Scheduling & future task management |

68+ MCP servers provide domain-specific tooling (finance, academic, web3, data science, etc.).
Three background workers handle long-running tasks: research, shadow lab (hypothesis testing),
and synthesis (report generation).

## Repository Structure

```
services/            # 7 microservices (api_gateway, orchestrator, mcp_host, rag_service, vault, swarm_manager, chronos)
shared/              # Foundation library (config, schemas, messaging, database, llm, mcp, hardware, logging, etc.)
mcp_servers/         # 68+ MCP tool servers organized by domain
workers/             # Background processors (research_worker, shadow_lab_worker, synthesis_worker)
tests/               # Test suite (unit, integration, real, stress, simulation, mcp, verify)
configs/             # YAML configs (prompts, settings, tool_registry, prometheus, grafana, alerting)
migrations/          # Alembic database migrations
k8s/                 # Kubernetes manifests
references/          # Jupyter reference notebooks
```

## Build & Dependencies

Package manager: **uv** (preferred), pip as fallback. Build backend: hatchling.
Wheel packages: `services`, `mcp_servers`, `shared`, `workers`.

```bash
# Install all dependencies
uv sync

# Install with dev extras
uv sync --extra dev
```

Key runtime dependencies: FastAPI, uvicorn, Pydantic v2, LangGraph, langchain-core, openai
(OpenRouter compatible), SQLAlchemy (async), asyncpg, pgvector, pandas, duckdb, playwright,
structlog, OpenTelemetry, prometheus-client, mcp.

Infrastructure: PostgreSQL 16 with pgvector extension, Prometheus, Grafana.

## Common Commands

```bash
# Run a service locally
uv run python -m services.<service_name>.main

# Run database migrations
uv run alembic upgrade head

# Start full stack via Docker
docker-compose up -d

# Lint
uv run ruff check .

# Auto-format
uv run ruff format .

# Type check
uv run mypy .

# Run all tests
uv run pytest tests/ -v

# Run unit tests only
uv run pytest tests/unit/ -v

# Run stress test with a query
uv run pytest tests/stress/stress_test.py --query="Analyze Tesla's 2024 VPP strategy" -v -s
```

## Testing

Framework: pytest with async support (`asyncio_mode = auto`). Test paths: `tests/`.

Markers:
- `@pytest.mark.unit` — Fast, mocked, no external dependencies
- `@pytest.mark.integration` — Requires running services
- `@pytest.mark.mcp` — MCP protocol tests (require API)
- `@pytest.mark.stress` — Load/stress tests
- `@pytest.mark.slow` — Time-intensive tests
- `@pytest.mark.simulation` — Chaos/failure simulation with real API calls

Configuration is in both `pytest.ini` and `pyproject.toml [tool.pytest.ini_options]`.
Default addopts: `-v --tb=short --strict-markers`.

## Code Quality

**Ruff** (linter + formatter):
- Line length: 100 (E501 ignored)
- Target: Python 3.11
- Rules: E, F, I, N, W, UP

**MyPy** (type checker):
- Strict mode enabled
- `ignore_missing_imports = true`

## Code Conventions

- **Files**: `snake_case` (e.g., `artifact_bus.py`)
- **Classes**: `PascalCase` (e.g., `ArtifactBus`)
- **Functions**: `snake_case` (e.g., `process_artifact`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Type hints**: Required on all functions
- **Async/await**: Required for all I/O operations
- **Pydantic models**: Required for data validation and contracts
- **Structured logging**: Use `structlog` consistently
- **Error handling**: Meaningful exception messages, proper handling

## Architecture Principles

1. **Microservice isolation** — Services communicate only via APIs, never shared filesystem
2. **Vault-centric data flow** — All persistent data flows through the Vault service
3. **Zero-trust hardware** — Code adapts to hardware via `shared/hardware/` detection layer
4. **Split-brain governance** — Reasoning (Orchestrator) is separated from execution (MCP Host)
5. **Stateless services** — Services pull state from Vault over the network; no local disk dependency
6. **Service registry** — Dynamic URL resolution via `shared/autodiscovery.py`

## Environment Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | LLM provider API key |
| `OPENROUTER_MODEL` | Default model (e.g., `nvidia/nemotron-3-nano-30b-a3b:free`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Optional Redis for caching |
| `JWT_SECRET` | Auth token secret for API Gateway |
| `TAVILY_API_KEY` | Optional search API |
| `BRAVE_API_KEY` | Optional search API |
| `ENVIRONMENT` | `development` or `production` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARN`, `ERROR` |

## Docker

Multi-stage `Dockerfile` with targets for each service plus a `development` all-in-one target.
`docker-compose.yml` orchestrates all 7 services, a research worker, PostgreSQL 16 (pgvector),
Prometheus, and Grafana.

```bash
docker-compose up -d          # Start everything
docker-compose up postgres    # Start only database
docker-compose logs -f <svc>  # Follow service logs
```

## Database Migrations

Managed by Alembic. Config in `alembic.ini`, migration scripts in `migrations/versions/`.

```bash
uv run alembic upgrade head          # Apply all migrations
uv run alembic revision --autogenerate -m "description"  # Create new migration
uv run alembic downgrade -1          # Rollback one migration
```

## Key Shared Library Modules

| Module | Purpose |
|--------|---------|
| `shared/config.py` | Centralized settings via environment variables |
| `shared/schemas.py` | Pydantic domain models & data contracts |
| `shared/messaging.py` | Event bus for inter-service communication |
| `shared/dispatcher.py` | PostgreSQL-backed persistent task queue |
| `shared/context_pool.py` | Shared memory segments across agents |
| `shared/autodiscovery.py` | Dynamic service discovery & URL resolution |
| `shared/hardware/` | Hardware detection & adaptive execution scaling |
| `shared/database/` | Connection pooling & lifecycle management |
| `shared/logging/` | OpenTelemetry & structured logging setup |
| `shared/llm/` | Multi-provider LLM abstraction layer |
| `shared/mcp/` | Model Context Protocol client implementation |
| `shared/embedding/` | Vector generation for semantic search |

## Security

- Never hardcode secrets or API keys; use environment variables
- All external inputs validated via Pydantic
- Zero-trust model for inter-service communication
- Every tool call logged and gated by Swarm Manager
- JWT-based auth at the API Gateway

## When Making Changes

1. Identify which microservice owns the functionality
2. Check `shared/` for existing utilities before writing new ones
3. Follow existing patterns in the surrounding code
4. Use type hints, async/await, Pydantic models, and structlog
5. Consider how changes affect the DAG execution flow
6. Run `uv run ruff check .` and `uv run mypy .` before committing
