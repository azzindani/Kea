# 🗄️ RAG Service ("The Library")

The **RAG (Retrieval-Augmented Generation) Service** provides the global knowledge orchestration layer for Kea. It functions as the **Librarian**, managing access to massive external datasets and multiple distinct RAG backends via a unified API.

## 📐 Architecture

The RAG Service operates as a **Federated Search Abstraction**. It decouples the source of information (Hugging Face, Local PDFs, Web Scrapes) from the Kernel's retrieval needs.

```mermaid
graph TD
    subgraph RAG [RAG Service]
        direction TB
        API[FastAPI: /facts/search] --> Orch[Retrieval Orchestrator]
        Orch --> Hybrid[Hybrid Search Engine]
        
        Hybrid --> Vector[Vector Store: Qdrant/pgvector]
        Hybrid --> Meta[Metadata Filter]
        Hybrid --> Ingest[Dataset Ingestor]
    end

    subgraph Sources [External Sources]
        Ingest --> HF[Hugging Face Datasets]
        Ingest --> Local[Local Artifact Bus]
    end
```

### Component Overview

| Component | Responsibility | Cognitive Role |
| :--- | :--- | :--- |
| **Retrieval Orch** | Coordinates federated search across backends. | Semantic Search |
| **Hybrid Engine** | Combines vector distance with metadata tagging. | Fact Retrieval |
| **Dataset Ingestor**| Streams and indexes massive HF datasets. | Knowledge Ingestion |
| **Metadata Store** | Manages tags (Source, Confidence, Time). | Relational Context |

---

## ✨ Key Features

### 1. Atomic Fact Model
Every finding in Kea is normalized into an `AtomicFact` (Entity-Attribute-Value). This normalization allows the Orchestrator's **Consensus Engine** to compare findings from different sources at a granular level, resolving contradictions before they reach the final report.

### 2. High-Throughput Ingestion
The `DatasetLoader` streams rows from Hugging Face or the local **Artifact Bus**, maps them to the atomic schema, and batch-inserts them into the vector store. This allows Kea to "learn" about a new domain (e.g., 10,000 regulatory documents) in minutes.

### 3. Provenance & Citation Tracking
Every fact stored in the Library maintains a strict association with its source URL, document title, and extraction timestamp. This ensures that every claim in a Kea-generated report can be traced back to a specific, verified origin.

---

## 📁 Codebase Structure

- **`main.py`**: FastAPI entrypoint hosting the facts, datasets, and knowledge API.
- **`core/`**: The implementation of the storage and loading logic.
    - `fact_store.py`: The concrete implementation of the `FactStore` protocol.
    - `knowledge_store.py`: Semantic search for system-level knowledge (skills/rules).
    - `dataset_loader.py`: Integration with Hugging Face `datasets` for JIT ingestion.
    - `artifact_store.py`: Interface for high-fidelity research data persistence.

---

## 🧠 Deep Dive

### 1. Federated Semantic Search
When the Kernel requests a fact, the RAG service doesn't just check one database. It performs **Composite Retrieval**:
1.  **Global Knowledge**: Checks the long-term knowledge base.
2.  **Job Context**: Checks the private fact store for the current research session.
3.  **Metadata Overlay**: Filters results by time-period and confidence thresholds.

### 2. Contradiction Detection
The Library uses semantic clustering to identify contradictory facts (e.g., Source A says "Price is $10" while Source B says "Price is $12"). These are flagged for the **Keeper Node** in the Orchestrator to resolve during the "Context Hygiene" phase.

---
*The RAG Service provides the evidence that grounds Kea's reasoning in physical reality.*

