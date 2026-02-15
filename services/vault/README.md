# 🏦 The Vault ("The Black Box")

The **Vault Service** is the research persistence, context, and data transport layer of the Kea v0.4.0 system.

> [!NOTE]
> In the **Brain vs Body** architecture, the Vault is a "Body" service. It provides the persistent storage and artifact bus supporting the **Kea Kernel**.

## ✨ Features

- **Immutable Audit Trail**: Logs all system events with SHA-256 checksums to prevent record tampering.
- **The Artifact Bus**: Serves as the central "Conveyor Belt" for moving data artifacts between independent agents and nodes.
- **LangGraph Checkpointing**: Persists the state of research graphs to PostgreSQL, enabling seamless recovery after system restarts or crashes.
- **Cryptographic Integrity**: Each audit entry is hashed with its predecessor's metadata, creating a verifiable chain of custody for research findings.
- **High-Fidelity "OODA" Logging**: Specifically captures Observe, Orient, Decide, and Act phases for every agent decision.
- **Automatic Auditing Decorator**: Easy-to-use `@audited` utility for developers to wrap sensitive functions with persistence logic.

## 📐 Architecture

The Vault sits at the bottom of the stack, providing a "Source of Truth" for all other services.

### 🗼 The Persistence Flow

```mermaid
graph TD
    Orch[Orchestrator] -->|Event| API[Vault API]
    API --> Trail[Audit Trail Manager]
    Trail -->|Hash| Checksum[Checksum Generator]
    Checksum -->|Verify| Postgres[(PostgreSQL)]
    
    Orch -->|State Snapshot| Checkpoint[Checkpoint Store]
    Checkpoint -->|JSONB| Postgres
    
    Nodes[Generative Agents] -->|Artifacts| Bus[Artifact Bus]
    Bus -->|Store| S3[Blob Storage / MinIO]
    Bus -->|Index| Postgres
    
    Admin[Admin Console] -->|Query| API
    API -->|Read| Postgres
```

## 📁 Codebase Structure

- **`main.py`**: FastAPI entrypoint hosting the audit and checkpointing API.
- **`core/`**: The implementation of the persistence engines.
    - `audit_trail.py`: Core logic for managing `AuditEntry` objects and checksum verification.
    - `checkpointing.py`: Implementation of the PostgreSQL-backed state store for LangGraph.
    - `postgres_audit.py`: Direct database interactions for the audit trail.
    - `postgres_store.py`: General-purpose relational storage management.
    - `vector_store.py`: Interface for high-dimensional storage (used by other services for raw embeddings).
    - `artifact_bus.py`: Manages the transport of large data artifacts between services.
    - `encryption.py`: Handling of cryptographic operations for data security.

## 🧠 Deep Dive

### 1. Immutable Audit Entries
The `AuditEntry` is the unit of accountability in Kea. Beyond standard fields (Action, Actor, Resource), it calculates a unique `checksum` of its own contents. Any attempt to modify a log entry post-creation will invalidate this checksum, providing a mathematically verifiable audit trail for regulated industries (Finance, Legal, Healthcare).

### 2. LangGraph State Checkpointing
The `CheckpointStore` allows Kea to handle long-running research jobs (minutes to hours). Every time the Orchestrator moves between nodes (e.g., from Planner to Researcher), a state snapshot is saved as a `JSONB` blob in the `graph_checkpoints` table. If the system fails, the Orchestrator can reload the `latest` checkpoint and resume exactly where it left off.

### 3. The Artifact Bus & Active Context
In the Kea v4.0 architecture, research data is not shared via local filesystems. Instead, collected "Active Artifacts" (e.g., a 10MB webscrape or a downloaded PDF) are placed onto the **Artifact Bus**. The Vault manages the storage and **vector indexing** of these artifacts. This allows the Orchestrator and downstream tools to perform semantic searches over the *currently collected data* for a specific job, rather than relying only on global knowledge or polluting the LLM context.

## 📚 Reference

### Audit Event Types

| Event Type | Description | Trigger Point |
|:-----------|:------------|:--------------|
| `TOOL_CALLED` | Execution of an MCP tool | Researcher Node |
| `DECISION_MADE` | Agent selecting a specific research path | Planner Node |
| `SECURITY_CHECK` | Compliance engine validation | Swarm Manager |
| `APPROVAL_GRANTED`| Human sign-off on high-risk task | API Gateway |

### API Interface

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/audit/logs` | `POST` | Manually log a custom audit event. |
| `/audit/logs` | `GET` | Query and filter audit history. |
| `/checkpoints/{job_id}` | `GET` | Retrieve the state of a specific research job. |
| `/health` | `GET` | Service status and DB connection pool health. |
