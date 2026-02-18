# 🏦 The Vault ("The Memory")

The **Vault Service** is the research persistence and data transport layer of the Kea v0.4.0 system. It serves as the system's **Long-Term Memory** and **Immutable Audit Trail**.

## 📐 Architecture

The Vault provides a unified interface for three distinct persistence needs: **Audit Logs**, **Graph Checkpoints**, and **Research Artifacts**.

```mermaid
graph TD
    subgraph Vault [Vault Service]
        direction TB
        API[FastAPI: /vault] --> Trail[Audit Trail Manager]
        API --> Checkpoint[State Checkpointer]
        API --> Bus[Artifact Bus]
        
        Trail -->|Hashes| Postgres[(PostgreSQL)]
        Checkpoint -->|Snapshots| Postgres
        Bus -->|Storage| S3[Object Storage / MinIO]
    end

    Orchestrator -->|State| Checkpoint
    Researchers -->|Data| Bus
    SwarmManager -->|Logs| Trail
```

### Component Overview

| Component | Responsibility | Cognitive Role |
| :--- | :--- | :--- |
| **Audit Trail** | Immutable logging of every system decision. | Procedural Memory |
| **State Checkpointer**| Persistent snapshots of LangGraph states. | Working Memory |
| **Artifact Bus** | High-speed transport for research files. | Sensory Buffet |
| **Integrity Mgr** | Cryptographic verification of log entries. | Conscience |

---

## ✨ Key Features

### 1. Immutable Audit Trail
The Vault calculates a SHA-256 checksum for every decision made by the system. These logs are "Chained" (each entry contains the hash of the previous one), creating a mathematically verifiable record of research provenance for regulated industries.

### 2. LangGraph State Checkpointing
The **State Checkpointer** allows Kea to handle missions that last for hours. Every node transition in the **Orchestrator** is saved as a `jsonb` blob. If the system experiences a power failure or restart, it can resume from the exact last transition point.

### 3. The Artifact Bus (Architecture)
While the Vault doesn't have a file named `artifact_bus.py`, the **Vector Store** and **Postgres Store** act together to serve this function. Heavy artifacts are stored as `Documents` in the vector database, allowing agents to retrieve massive files via semantic search rather than downloading them locally.

---

## 📁 Codebase Structure

- **`main.py`**: FastAPI entrypoint hosting the persistence and state APIs.
- **`core/`**: The implementation of the immutable storage engines.
    - `audit_trail.py`: Logic for `AuditEntry` creation and hash-chaining.
    - `checkpointing.py`: Implementation of the Postgres-backed LangGraph state store.
    - `postgres_store.py`: General-purpose relational storage management.
    - `vector_store.py`: Interface for high-dimensional semantic search.

---

## 🧠 Deep Dive

### 1. The "Black Box" Principle
The Vault is designed as a "Write-Once, Read-Many" system for audit data. Once an entry is committed, it cannot be modified or deleted via the API. This ensures that even if an agent "hallucinates" or a service is compromised, the history of what actually happened remains pristine.

### 2. Checkpoint Hybrid Recovery
When a job resumes, the Vault provides the **Full Context Snapshot**. This includes not just the current node, but the entire history of `AtomicFact` objects and research variables collected up to that point, ensuring that the **Kernel** has 100% "Contextual Awareness" upon restart.

---
*The Vault ensures that no finding is lost and every decision is accountable.*

