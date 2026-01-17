# RAG Service ("The Memory")

The RAG Service manages the "Triple Vault" memory architecture of Kea. It provides fast retrieval of atomic facts, storage of complex artifacts, and semantic search capabilities to ground the agents.

## 🏗️ Architecture

The memory system is divided into three distinct tiers:

1.  **Atomic Facts (Vector Store)**: Stores discrete "Fact Objects" (Entity-Attribute-Value) for rapid semantic retrieval.
2.  **Episodic Logs**: Stores sequential conversation history and audit trails.
3.  **Artifact Store**: Stores heavy files (PDFs, Parquet, CSVs) generated during Deep Research.

## 🧩 Codebase Reference

### 1. Service Entry
| File | Description | Key Classes/Functions |
|:-----|:------------|:----------------------|
| `main.py` | FastAPI application for the RAG service. Defines routes for adding/searching facts and health checks. Manages global lifecycle of stores. | `app`, `add_fact()`, `search_facts()` |

### 2. Core Logic (`/core`)
| File | Description | Key Classes/Functions |
|:-----|:------------|:----------------------|
| `vector_store.py` | **Vector DB Interface**. Abstract wrapper around Qdrant/Chroma. Handles embedding generation and similarity search. | `VectorStore` |
| `artifact_store.py` | **Blob Storage**. Manages heavy binary files (Parquet, PDFs). Abstracts S3 or local file system operations. | `ArtifactStore` |
| `fact_store.py` | **Logic Layer**. Connects the API to the Vector Store. Handles the conversion of raw text into `AtomicFact` objects. | `FactStore` |
| `graph_rag.py` | **Knowledge Graph**. (Future) Module for connecting facts via relationships (edges) to allow graph traversal. | `KnowledgeGraph` |

### 3. API Routes
The service exposes the following endpoints:

| Endpoint | Method | Description | Payload Example |
|:---------|:-------|:------------|:----------------|
| `/facts` | `POST` | Ingest a new atomic fact. | `{ "entity": "Adaro", "attribute": "Revenue", "value": "$5B" }` |
| `/facts/search`| `POST` | Semantic search for facts. | `{ "query": "mining revenue", "limit": 5 }` |
| `/facts/{id}` | `GET` | Retrieve a specific fact by ID. | - |
| `/entities` | `GET` | List all unique entities in the database. | - |

## 🚀 Usage

This service usually runs as a sidecar or a separate microservice:

```bash
# Start the RAG API
python -m services.rag_service.main
```
