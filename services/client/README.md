# Research Client SDK

A robust Python client for the Project Research Platform. This SDK provides programmatic access to the research capabilities, handling authentication, job submission, polling, and result retrieval.

## Features

- **Automatic Authentication**: Handles login, registration, and JWT token refresh transparently.
- **Async API**: Fully asynchronous design using `httpx`.
- **Job Management**: Submit jobs, poll status, and retrieve structured results.
- **Metrics Collection**: Detailed tracking of token usage, tool efficiency, and resource consumption.

## CLI Usage

The quickest way to run a research job is via the included CLI tool:

```bash
# Run against local development environment
python services/client/cli.py --query "Analyze the impact of AI on healthcare" --env dev

# Enable verbose logging
python services/client/cli.py --query "Research Tesla's financial health" --verbose
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--query` | The research question or topic (Required) | - |
| `--env` | Environment to target (`dev`, `prod`, `local`) | `dev` |
| `--url` | Custom API URL (overrides `--env`) | - |
| `--verbose`, `-v` | Enable debug logging | `False` |

---

## programmatic Usage

You can use the SDK in your own Python applications (e.g., Streamlit, FastAPI, Scripts).

### 1. Basic Job Execution

```python
import asyncio
from services.client.api import ResearchClient
from services.client.runner import ResearchRunner
from services.client.metrics import MetricsCollector

async def main():
    # Initialize client
    client = ResearchClient(base_url="http://localhost:8000")
    await client.initialize()
    
    # Setup runner
    metrics = MetricsCollector()
    runner = ResearchRunner(client, metrics)
    
    # Run a research job
    print("Starting research...")
    job_metrics = await runner.run_query("Analyze the latest EV battery trends")
    
    if job_metrics.success:
        print("✅ Research Complete!")
        print(f"Duration: {job_metrics.duration_ms / 1000:.1f}s")
        print(f"Efficiency Ratio: {job_metrics.efficiency_ratio:.2f}")
    else:
        print(f"❌ Failed: {job_metrics.error}")
        
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Accessing Metrics

The `JobMetrics` object returned by `run_query` contains detailed performance data:

```python
# Access detailed metrics
print(f"LLM Calls: {job_metrics.llm_calls}")
print(f"Tool Iterations: {job_metrics.tool_iterations}")
print(f"Peak Memory: {job_metrics.peak_memory_mb:.1f} MB")

# Export to JSON
metrics.export("research_metrics.json")
```

### 3. Custom Authentication

By default, the client uses test credentials. You can provide your own:

```python
client = ResearchClient(
    base_url="https://api.project.ai",
    email="myuser@example.com",
    password="secure_password",
    name="My User"
)
```

## Structure

- `api.py`: Core HTTP client and authentication logic.
- `runner.py`: High-level job orchestration (submit -> poll -> result).
- `metrics.py`: Performance tracking and stats collection.
