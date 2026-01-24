# ⏳ Chronos Service ("The Timekeeper")

**Chronos** is the planned temporal orchestration layer of Kea. It is intended to manage scheduled research jobs and recurring tasks.

> [!NOTE]
> **Current Status**: Chronos is currently a **placeholder service**. It provides a base FastAPI structure and a health check endpoint, but the scheduler and historian logic are pending implementation.

---

## 🏗️ Architecture: Ephemeral Coordination

In the current Kea topology, **Chronos** serves as the **Ephemeral Job Coordinator**. While its logic is natively integrated into the API Gateway's `JobStore`, it provides the system's "Temporal Backbone":

1.  **State Consistency**: Ensures jobs transition atomically from `PENDING` → `RUNNING` → `COMPLETED` utilizing Postgres's ACID properties.
2.  **Background Orchestration**: Leverages FastAPI's `BackgroundTasks` to decouple high-latency research jobs from user request-response cycles.
3.  **Concurrency Governance**: Manages job-level parallelism through the Orchestrator Service Registry, preventing overwhelming upstream MCP workers.

```mermaid
graph LR
    API[API Gateway] -->|Transaction| DB[Shared Context DB]
    API -->|Dispatch| Chronos[Chronos (Internal Node)]
    Chronos -->|Monitor| Job[Active Research Task]
    Job -->|Callback| DB
```

---

## ✨ Features & Consistency Logic

- **Atomic Job Transitions**: Every state change (e.g., `RUNNING` to `FAILED`) is logged with a UTC timestamp and an error payload if applicable.
- **Time-Limited Execution**: Implements a 600s hard timeout on research operations to prevent "Zombie Agents" from consuming system resources indefinitely.
- **Progress Tracking**: Provides a incremental `progress` scalar (0.0 - 1.0) accessible via the `/jobs/{id}` endpoint.
- **Artifact Binding**: Automatically maps generated Parquet, PDF, or JSON files to the parent `job_id` for one-stop retrieval.

---

## 📁 Codebase Structure

| File / Directory | Component | Description |
|:-----------------|:----------|:------------|
| **`main.py`** | **Entry Point** | Base FastAPI application (Port 8006). |
| **`core/`** | **Logic** | Placeholder for future orchestration logic. |

---

## 🔌 API Reference

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | `GET` | Basic service health check. |
