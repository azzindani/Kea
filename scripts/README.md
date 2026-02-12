# 📜 Utility Scripts

The `scripts/` directory contains various internal tools and administration scripts for managing the Kea v4.0 development lifecycle.

## 📁 Contents

- **`cli.py`**: A unified Command Line Interface for interacting with the Kea system from the terminal. Supports starting services, running one-off research jobs, and system diagnostics.
- **`standardize_init.py`**: A developer utility that ensures all `__init__.py` files across the repository follow the Kea v4.0 boilerplate standard (docstrings, imports, and `__all__` definitions).

## 🚀 Usage

### 1. Kea CLI
The CLI is the preferred way to interact with the system during development.

```bash
# Start all core services
uv run python scripts/cli.py start-all

# Run a quick research query
uv run python scripts/cli.py query "Who is the CEO of Tesla?"

# Check system health
uv run python scripts/cli.py doctor
```

### 2. Standardizing Imports
When adding new modules, run this script to ensure the `__init__.py` files are properly populated.

```bash
uv run python scripts/standardize_init.py ./services/orchestrator
```

## 🛠️ Development Note
These scripts are intended for **developers and operators**. They should NOT be used in production Kubernetes environments, where `kubectl` and service manifests are the primary management tools.
