# ⏳ Chronos Service ("The Timekeeper")

**Chronos** is the planned temporal orchestration layer of Kea v0.4.0.

> [!NOTE]
> In the **Brain vs Body** architecture, Chronos is a "Body" service. It coordinates timing and scheduling for the **Kea Kernel**.

> [!NOTE]
> **Current Status**: Chronos is currently a **placeholder service**. It provides a base FastAPI structure and a health check endpoint, but the scheduler and historian logic are pending implementation.

## ✨ Features (Planned)

- **Atomic Job Transitions**: Ensures jobs transition atomically from `PENDING` → `RUNNING` → `COMPLETED` utilizing Postgres's ACID properties.
- **Background Orchestration**: Leverages asynchronous task processing to decouple high-latency research jobs from user request-response cycles.
- **Concurrency Governance**: Manages job-level parallelism to prevent overwhelming upstream microservices and MCP workers.
- **Time-Limited Execution**: Implements hard timeouts on research operations to prevent "Zombie Agents" from consuming system resources indefinitely.
- **Progress Tracking**: Provides a incremental progress scalar (0.0 - 1.0) for real-time monitoring of long-running tasks.
- **Artifact Binding**: Automatically maps generated artifacts (Parquet, PDF, etc.) to their parent `job_id`.

## 📐 Architecture

In the current Kea topology, **Chronos** serves as the **Ephemeral Job Coordinator**. While its logic is natively integrated into the API Gateway's `JobStore` for the initial implementation, it is architected to become the system's "Temporal Backbone".

```mermaid
graph LR
    API[API Gateway] -->|Transaction| DB[Shared Context DB]
    API -->|Dispatch| Chronos[Chronos (Internal Node)]
    Chronos -->|Monitor| Job[Active Research Task]
    Job -->|Callback| DB
```

### Future Design
Chronos will transition to a distributed task scheduler (potentially using `apscheduler` or similar) that can survive service restarts and manage complex retry logic for failed research nodes.

## 📁 Codebase Structure

The directory structure is designed for modular expansion as the scheduling logic is implemented.

- **`main.py`**: The entrypoint for the service. Currently hosts a minimal FastAPI application on Port 8006.
- **`core/`**: Intended for the core scheduling engine, recurrence logic, and state transition management.
- **`README.md`**: Documentation of the service's purpose and future roadmap.

## 🧠 Deep Dive: Temporal Governance

### State Consistency
The primary responsibility of Chronos is to ensure that no research job remains in an undefined state. It will implement a "watchdog" pattern that periodically audits the `JobStore` for jobs that have exceeded their timeout or whose worker nodes have disconnected without reporting a final status.

### Concurrency & Backpressure
Chronos will act as a traffic controller, monitoring the load on the `MCP Host` and `Orchestrator`. It will implement backpressure mechanisms to queue new research requests when the system is operating at peak capacity.

## 📚 Reference

### API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | `GET` | Basic service health check. |

### Planned Configuration
- `MAX_JOB_DURATION`: Default 600s.
- `SCHEDULER_BACKEND`: Postgres.
- `CLEANUP_INTERVAL`: 3600s for purging old job logs.
