This is the best way to handle documentation for a system this complex. We will structure the `README.md` as a **Master Architecture Document**.

Here is **Part 1: The General Architecture & Core Philosophy**. This section establishes the high-level map and the "Router" logic that governs the entire system.

You can create a file named `ARCHITECTURE.md` or put this at the top of your `README.md`.

***

# 🦜 Kea: Distributed Autonomous Research Engine (DARE)

> **"Not just a Chatbot. A Research Factory."**

**Kea** is a microservice-based, recursive AI architecture designed for open-ended domain investigation. Unlike linear RAG systems, Kea utilizes a **Cyclic State Graph** to mimic human research behavior: formulating hypotheses, gathering data, verifying consistency, and autonomously reformulating strategies when results are suboptimal.

It separates **Reasoning** (The Brain/LLM) from **Execution** (The Muscle/Python), ensuring mathematical precision and hallucination-proof results.

---

## 🗺️ 1. The General Architecture (High-Level Map)

The system follows a **Hub-and-Spoke Microservices Pattern**. The central Orchestrator manages the lifecycle of a request, delegating work to specialized, isolated services via gRPC/REST.

```mermaid
graph TD
    %% --- STYLES ---
    classDef brain fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef router fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef memory fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;
    classDef tool fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    User(("User / API")) -->|Query| Gateway["API Gateway & Rate Limiter"]
    Gateway --> Router{"Intention Router"}

    %% --- THE ROUTING LAYER ---
    Router --"Simple Q"--> FastRAG["⚡ Fast RAG / Memory"]
    Router --"Methodology Q"--> Provenance["🔍 Provenance Graph"]
    Router --"Recalculation"--> ShadowLab["🧮 Shadow Lab (Sandbox)"]
    Router --"Deep Research"--> Orchestrator["🧠 Main Orchestrator"]

    %% --- THE DEEP RESEARCH LOOP ---
    subgraph CognitiveCore ["The Cognitive Core"]
        Orchestrator --> Planner["📝 Planner & Decomposer"]
        Planner --> Keeper["🛡️ The Keeper (Context Guard)"]
        Keeper --> Divergence["✨ Divergence Engine (Analysis)"]
        Divergence --> Synthesizer["✍️ Report Synthesizer"]
    end

    %% --- THE TOOLS LAYER (The Muscle) ---
    subgraph Tools ["Tool Microservices"]
        Scraper["🕷️ Robotic Scraper"]:::tool
        Analyst["🐍 Python Analyst"]:::tool
        Meta["📊 Meta-Analysis"]:::tool
    end

    %% --- THE MEMORY LAYER (The Vault) ---
    subgraph MemoryVault ["The Triple-Vault Memory"]
        Atomic["Atomic Facts DB"]:::memory
        Episodic["Episodic Logs"]:::memory
        Artifacts["Parquet/Blob Store"]:::memory
    end

    %% --- CONNECTIONS ---
    Orchestrator <--> Scraper
    Orchestrator <--> Analyst
    Divergence <--> Atomic
    Scraper --> Artifacts
    Analyst --> Artifacts
```

---

## 🚦 2. Pipeline Routing Logic

Kea does not treat every query the same. It uses an **Intention Router** to determine the most efficient execution path.

### Path A: The "Memory Fork" (Incremental Research)
*   **Trigger:** User asks a question partially covered by previous research.
*   **Logic:**
    1.  **Introspection:** The Planner decomposes the query into atomic facts ($A, B, C$).
    2.  **Vector Lookup:** Checks `Atomic Facts DB` for $A, B, C$.
    3.  **Gap Analysis:**
        *   Found $A$ (Confidence > 0.9).
        *   Missing $B, C$.
    4.  **Delta Plan:** The system generates a research task *only* for $B$ and $C$, ignoring $A$.
*   **Outcome:** 50-80% reduction in API costs and latency.

### Path B: The "Shadow Lab" (Re-Calculation)
*   **Trigger:** User asks to modify a parameter of a previous result (e.g., "What if growth is 10% instead of 5%?").
*   **Logic:**
    1.  **Artifact Retrieval:** The system retrieves the clean `data.parquet` file from the `Artifacts Store` (S3/HuggingFace).
    2.  **Code Injection:** The system sends the data + the new parameter to the **Python Sandbox**.
    3.  **Execution:** Python recalculates the specific formula.
*   **Outcome:** Instant answer with zero new web scraping.

### Path C: The "Grand Synthesis" (Meta-Analysis)
*   **Trigger:** User asks to combine multiple research jobs (e.g., "Combine the Market Study and the Regulatory Study").
*   **Logic:**
    1.  **Librarian Fetch:** Retrieves `Job_ID_1` and `Job_ID_2` from the Manifest.
    2.  **Schema Alignment:** The **Analyst Agent** writes Python code to normalize columns (e.g., mapping `revenue_usd` to `rev_global`).
    3.  **Fusion:** Executes a `pd.concat` or merge operation.
    4.  **Conflict Check:** The **Divergence Engine** highlights where Job 1 contradicts Job 2.

```mermaid
graph TD
    %% --- STYLES ---
    classDef trigger fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef decision fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef action fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef output fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- MAIN FLOW ---
    User(("User Input")):::trigger --> Router{"Intention Classifier<br/>(LLM Router)"}:::decision

    %% --- PATH A: THE MEMORY FORK (Incremental) ---
    subgraph PathA ["Path A: Incremental Research"]
        Router --"Follow-up / Update"--> VectorCheck["🔍 Check Atomic Facts DB"]
        VectorCheck --"Data Found"--> CacheHit["✅ Retrieve from Memory"]
        VectorCheck --"Data Missing"--> GapDetector{"Gap Analysis"}
        GapDetector -->|Only Search Missing| DeltaPlan["📉 Delta Planner"]
    end

    %% --- PATH B: THE SHADOW LAB (Recalculation) ---
    subgraph PathB ["Path B: Shadow Lab"]
        Router --"Recalculate / Modify"--> Loader["📂 Load .parquet Artifact"]
        Loader --> Sandbox["🐍 Python Sandbox<br/>(Execute New Formula)"]
    end

    %% --- PATH C: THE GRAND SYNTHESIS (Meta-Analysis) ---
    subgraph PathC ["Path C: Grand Synthesis"]
        Router --"Compare / Combine"--> Librarian["📚 Librarian<br/>(Fetch Job Manifests)"]
        Librarian --> Alchemist["⚗️ The Alchemist<br/>(Schema Alignment & Merge)"]
    end

    %% --- PATH D: DEEP RESEARCH (Fallback) ---
    subgraph PathD ["Path D: Zero-Shot Research"]
        Router --"New Topic"--> Planner["🧠 Full OODA Loop Planner"]
    end

    %% --- CONVERGENCE ---
    CacheHit --> Synthesizer
    DeltaPlan --> Scraper["🕷️ Robotic Scraper"]
    Scraper --> Synthesizer
    Sandbox --> Synthesizer
    Alchemist --> Synthesizer["✍️ Final Synthesis"]:::output
    Planner --> Scraper

```

---

## 🧬 3. Sub-Architectures (The "How-To")

### A. The "Keeper" Protocol (Context Immune System)
*Goal: To prevent the "Rabbit Hole" effect and hallucinations.*

```mermaid
sequenceDiagram
    participant Scraper as Robotic Scraper
    participant Quarantine as Quarantine Zone
    participant Keeper as The Keeper
    participant Brain as Orchestrator

    Scraper->>Quarantine: Ingest Raw Text (Chunked)
    loop Every Chunk
        Quarantine->>Keeper: Send Vector(Chunk)
        Keeper->>Keeper: Calc Cosine Similarity(User_Intent, Chunk)
        alt Similarity < 0.75 (Drift Detected)
            Keeper-->>Quarantine: 🔥 INCINERATE (Ignore)
        else Similarity > 0.75
            Keeper->>Brain: Release to Context
        end
    end
```

### B. The "Divergence Engine" (Abductive Reasoning)
*Goal: To investigate why data doesn't match expectations.*

```mermaid
graph LR
    Hypothesis(Expected: Revenue UP) --Collision--> Reality(Observed: Revenue DOWN)
    Reality --> Trigger{Divergence Type?}
    
    Trigger --"Numbers Wrong?"--> AgentA[Data Scientist: Normalize Units]
    Trigger --"Missing Factor?"--> AgentB[News Scout: Find Disruptions]
    Trigger --"Bias?"--> AgentC[Judge: Check Source Credibility]
    
    AgentA --> Synthesis
    AgentB --> Synthesis
    AgentC --> Synthesis
    Synthesis --> FinalReport[Explained Contradiction]
```

---

## 🛠️ Technology Stack

| Component | Tech | Role |
| :--- | :--- | :--- |
| **Orchestrator** | **Python / LangGraph** | Cyclic state management and consensus loops. |
| **API Interface** | **FastAPI** | Asynchronous microservice communication. |
| **Analysis** | **Pandas / DuckDB** | In-memory SQL/Dataframe manipulation for "Shadow Lab". |
| **Memory** | **Qdrant + GraphRAG** | Storage of atomic facts and their relationships. |
| **Storage** | **Parquet / S3** | Efficient storage of "Artifacts" (Raw DataFrames). |
| **Isolation** | **Docker / E2B** | Sandboxed code execution environment. |
| **Browser** | **Playwright** | Headless, stealthy web scraping with vision capabilities. |

---

## 🧠 4. The Cognitive Core & Workflow Logic

Kea differs from standard agents by implementing a **"Meta-Cognitive" Layer**. It does not simply execute a prompt; it *designs* the prompt required to execute the task, then critiques the result.

### 4.1. The "Meta-Prompt" Layer (System Prompt Definer)

To optimize for **cost** and **accuracy**, Kea uses a hierarchical model strategy. A cheaper "Architect Model" defines the persona for the "Worker Model."

**The Logic:**
1.  **Task Analysis:** The Planner receives a sub-task (e.g., "Extract financial ratios for Adaro 2024").
2.  **Persona Injection:** The Architect generates a specific System Prompt.
    *   *Input:* "Task: Finance extraction. Domain: Mining."
    *   *Generated Prompt:* "You are a Forensic Accountant. You ignore marketing fluff. You only output JSON. You prioritize tables over text."
3.  **Execution:** The Worker Model runs with this strict persona, reducing hallucinations.

```mermaid
sequenceDiagram
    participant Planner as 📝 Planner
    participant Architect as 🏗️ Architect (Small LLM)
    participant Worker as 👷 Worker (Large LLM)
    participant Tool as 🛠️ Python Tool

    Planner->>Architect: Send Task Context
    Note over Architect: Generates strict <br/>System Prompt
    Architect->>Worker: Inject Dynamic Persona
    Worker->>Tool: Execute Code/Search
    Tool-->>Worker: Return Raw Data
    Worker-->>Planner: Return Structured Result
```

---

### 4.2. The Consensus Engine (Adversarial Collaboration)

To prevent the "Yes-Man" problem (where AI blindly agrees with the first search result), Kea implements an **Adversarial Feedback Loop**. This simulates a boardroom meeting between three distinct personas.

**The Roles:**
1.  **The Generator (Optimist):** Gathers data and proposes an answer.
2.  **The Critic (Pessimist):** Scans the answer for logical fallacies, missing dates, or weak sources.
3.  **The Judge (Synthesizer):** Decides if the answer is "Market Ready" or needs "Revision."

**The Workflow:**

```mermaid
graph TD
    %% STYLES
    classDef role fill:#fff,stroke:#333,stroke-width:2px;
    classDef decision fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;

    Start((Start)) --> Generator["🤠 Generator (Gather Data)"]:::role
    Generator --> Output["Draft Report"]
    Output --> Critic["🧐 Critic (Audit & Attack)"]:::role
    
    Critic --> Review{Pass Audit?}:::decision
    
    Review --"No (Flaws Found)"--> Feedback["📝 Correction Instructions"]
    Feedback --> Generator
    
    Review --"Yes (Verified)"--> Judge["⚖️ Judge (Final Polish)"]:::role
    Judge --> Final((Final Output))
```

---

### 4.3. The OODA Loop (Recursive Planning)

Kea operates on the military **OODA Loop** (Observe, Orient, Decide, Act) to handle "Unknown Unknowns." The plan is not static; it evolves as data is discovered.

*   **Observe:** The system ingests raw data from the web.
*   **Orient:** The **Keeper** compares this data against the user's intent vector.
*   **Decide:** The **Divergence Engine** determines if the hypothesis holds.
    *   *If Hypothesis Fails:* The system triggers a **"Pivot"**.
*   **Act:** The system spawns new sub-agents based on the *new* hypothesis.

**Example Scenario:**
1.  *Hypothesis:* "Nickel prices are up, so Mine Revenue should be up."
2.  *Observation:* "Mine Revenue is down."
3.  *Orientation:* Divergence Detected.
4.  *Decision (Pivot):* "Investigate 'Production Volume' and 'Weather Events'."
5.  *Act:* Spawn `Weather_Agent` and `Production_Agent`.

```mermaid
graph TD
    %% --- STYLES ---
    classDef observe fill:#fab1a0,stroke:#333,stroke-width:2px,color:#333;
    classDef orient fill:#74b9ff,stroke:#333,stroke-width:2px,color:#fff;
    classDef decide fill:#a29bfe,stroke:#333,stroke-width:2px,color:#fff;
    classDef act fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef fail fill:#ff7675,stroke:#333,stroke-width:2px,color:#fff;

    %% --- 1. OBSERVE (The Senses) ---
    subgraph Phase1 ["Phase 1: OBSERVE (Execution)"]
        Planner("📝 Current Plan"):::act --> Trigger("🚀 Trigger Agents"):::act
        Trigger --> Scraper("🕷️ Robotic Scraper"):::observe
        Scraper --> RawData["📄 Raw Ingested Data"]:::observe
    end

    %% --- 2. ORIENT (The Context) ---
    subgraph Phase2 ["Phase 2: ORIENT (Context Check)"]
        RawData --> Keeper{"🛡️ The Keeper"}:::orient
        Keeper --"Drift Detected<br/>(Irrelevant)"--> Incinerator("🔥 Prune Branch"):::fail
        Keeper --"Context Valid"--> ContextData["✅ Contextualized Facts"]:::orient
    end

    %% --- 3. DECIDE (The Hypothesis) ---
    subgraph Phase3 ["Phase 3: DECIDE (Divergence Check)"]
        ContextData --> Divergence{"✨ Divergence Engine"}:::decide
        Divergence --"Hypothesis Confirmed"--> Success["🏁 Validated Fact"]:::decide
        Divergence --"Hypothesis FAILED"--> Collision("💥 Collision Detected"):::decide
    end

    %% --- 4. ACT (The Pivot) ---
    subgraph Phase4 ["Phase 4: ACT (Recursive Pivot)"]
        Collision --> Abductive{"🕵️ Why did it fail?"}:::act
        
        Abductive --"Missing Factor?"--> NewFactor["➕ Add Variable: Weather/Strike"]:::act
        Abductive --"Bad Data?"--> NewSource["🔄 Switch Source: Gov vs News"]:::act
        
        NewFactor --> RePlan("🔄 Reformulate Plan"):::act
        NewSource --> RePlan
    end

    %% --- THE LOOP ---
    RePlan -.->|Recursive Loop| Planner
    Success --> Synthesizer("✍️ Final Synthesis")

```
---

## 💾 5. Memory & Data Structures

To support **"Jarvis-like" Recall** and **Meta-Analysis**, Kea utilizes specific data schemas. We do not just store text; we store **Structured Artifacts**.

### 5.1. The "Atomic Fact" Schema (Vector DB)
Used for **Incremental Research** (The "Memory Fork"). This allows the system to recall specific numbers without reading full reports.

```json
{
  "fact_id": "uuid_v4",
  "entity": "Adaro Energy",
  "attribute": "Revenue",
  "value": "6.5 Billion",
  "unit": "USD",
  "period": "FY2024",
  "source_url": "https://adaro.com/report.pdf",
  "confidence_score": 0.98,
  "vector_embedding": [0.12, -0.88, 0.45, ...]
}
```
```mermaid
graph LR
    %% --- STYLES ---
    classDef raw fill:#dfe6e9,stroke:#333,stroke-width:2px,color:#333;
    classDef process fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef schema fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- INGESTION ---
    RawDoc["📄 Raw Document<br/>(PDF / HTML)"]:::raw --> Atomizer["⚛️ The Atomizer Agent<br/>(LLM Extractor)"]:::process

    %% --- THE SCHEMA TRANSFORMATION ---
    Atomizer --> FactJSON["🧩 Atomic Fact (JSON)"]:::schema
    
    subgraph SchemaDetail ["The Schema Structure"]
        FactJSON --"Entity: Adaro"--> F1["Entity"]
        FactJSON --"Attr: Revenue"--> F2["Attribute"]
        FactJSON --"Value: $6B"--> F3["Value"]
        FactJSON --"Time: 2024"--> F4["Period"]
    end

    %% --- STORAGE ---
    FactJSON --> Embedder["🧮 Embedding Model<br/>(Bi-Encoder)"]:::process
    Embedder --> VectorDB[("💠 Vector DB<br/>(Qdrant/Weaviate)")]:::db

    %% --- RETRIEVAL FLOW ---
    subgraph Recall ["Incremental Retrieval"]
        Query("User Query: Adaro Revenue") --> Search["🔍 Similarity Search"]:::process
        VectorDB <--> Search
        Search --"Match > 0.9"--> Hit["✅ Cache Hit"]:::schema
        Search --"No Match"--> Miss["❌ Gap Detected"]:::raw
    end
```

### 5.2. The "Conversation Project" Schema (JSON)
Used for **Grand Synthesis** and **Systematic Reviews**. This tracks the *provenance* of every job in a session.

```json
{
  "session_id": "sess_99",
  "topic": "Nickel Market Analysis",
  "jobs": [
    {
      "job_id": "job_01",
      "type": "market_research",
      "status": "completed",
      "artifacts": {
        "raw_data": "s3://bucket/sess_99/job_01_data.parquet",
        "report": "s3://bucket/sess_99/job_01_report.md",
        "code_snippets": ["s3://.../calc_cagr.py"]
      }
    },
    {
      "job_id": "job_02",
      "type": "regulatory_check",
      "status": "completed",
      "artifacts": {
        "raw_data": "s3://bucket/sess_99/job_02_data.parquet"
      }
    }
  ]
}
```
```mermaid
graph TD
    %% --- STYLES ---
    classDef root fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef job fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef artifact fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- THE ROOT SESSION ---
    Session["📁 Session Object (JSON)<br/>ID: sess_99"]:::root --> Topic["Topic: Nickel Market Analysis"]:::root
    Session --> JobList["Jobs Array"]:::root

    %% --- JOB 1: MARKET RESEARCH ---
    subgraph Job1 ["Job 01: Market Research"]
        JobList --> J1["Job ID: job_01<br/>Status: Completed"]:::job
        J1 --"Pointer"--> Art1["Artifacts Manifest"]:::artifact
        
        Art1 -.->|Path| S3_Data1[("☁️ S3: job_01_data.parquet<br/>(Raw Financials)")]:::storage
        Art1 -.->|Path| S3_Rep1[("☁️ S3: job_01_report.md<br/>(Text Summary)")]:::storage
        Art1 -.->|Path| Py_Code1[("☁️ S3: calc_cagr.py<br/>(Reproducible Code)")]:::storage
    end

    %% --- JOB 2: REGULATORY CHECK ---
    subgraph Job2 ["Job 02: Regulatory Check"]
        JobList --> J2["Job ID: job_02<br/>Status: Completed"]:::job
        J2 --"Pointer"--> Art2["Artifacts Manifest"]:::artifact
        
        Art2 -.->|Path| S3_Data2[("☁️ S3: job_02_laws.parquet<br/>(Legal Clauses)")]:::storage
    end

    %% --- THE CONSUMER ---
    Session --> Librarian{"📚 The Librarian"}:::root
    Librarian -->|Fetch All Parquet Files| Alchemist["⚗️ The Alchemist<br/>(Grand Synthesis)"]:::job
```
### 5.3. The "Shadow Lab" Workflow (Re-Calculation)
This architecture allows users to ask "What if?" questions without triggering new web searches.

1.  **User Request:** "Recalculate Job 1 assuming 10% inflation."
2.  **Loader:** Pulls `job_01_data.parquet` from S3.
3.  **Sandbox:** Loads Parquet into Pandas DataFrame.
4.  **Execution:** Runs `df['adjusted_revenue'] = df['revenue'] * 1.10`.
5.  **Output:** Returns table immediately. **Zero Web Requests.**

---
```mermaid
graph TD
    %% --- STYLES ---
    classDef input fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;
    classDef compute fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef sandbox fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;

    %% --- TRIGGER ---
    User("User: 'Recalculate Job 1 with 10% inflation'"):::input --> Router{"Intention Router"}:::input
    
    %% --- THE SHADOW LAB ISOLATION ---
    subgraph ShadowLab ["🔬 The Shadow Lab (Offline)"]
        
        Router --"Modify Param"--> Coder["👨‍💻 Code Generator<br/>(LLM)"]:::compute
        
        %% --- DATA LOADING ---
        Router --"Fetch Data"--> Loader["📂 Artifact Loader"]:::storage
        S3[("☁️ S3 Artifact Store<br/>(job_01_data.parquet)")]:::storage -.->|Load DataFrame| Loader
        
        %% --- EXECUTION ---
        Coder --"1. Generate Script"--> Sandbox["🐍 Python Sandbox<br/>(E2B / Docker)"]:::sandbox
        Loader --"2. Inject DataFrame"--> Sandbox
        
        Sandbox --"3. Execute"--> Result["📊 New Calculation Result"]:::sandbox
    end

    %% --- OUTPUT ---
    Result --> Output("Response: 'Adjusted Revenue is $7.1B'"):::input
    
    %% --- BYPASS VISUALIZATION ---
    Internet((Internet / Web))
    Router -.->|⛔ BYPASS| Internet
```

## 🤖 6. The Robotic Infrastructure (The "Hands")

To function as a true Deep Research Engine, Kea must navigate the modern, hostile web. It uses a **Stealth Robotic Fleet** to handle scraping, avoiding bans, and reading complex UIs.

### 6.1. The Headless Browser Fleet
Instead of simple HTTP requests (which get blocked), Kea controls a cluster of headless browsers.

*   **Technology:** Playwright (Python) + `stealth` plugins.
*   **Rotation Logic:**
    *   **User-Agent Rotation:** Mimics different devices (iPhone, Mac, Windows) per request.
    *   **IP Rotation:** Routes traffic through residential proxies if a 403 Forbidden is detected.
*   **Visual Scraping Protocol:**
    *   If `HTML Parsing` fails (due to dynamic JS or obfuscation), the system triggers **Vision Mode**.
    *   **Snapshot:** Takes a screenshot of the viewport.
    *   **Vision Model:** Sends image to GPT-4o-Vision/Gemini-Pro-Vision with prompt: *"Extract the table data from this image into JSON."*

```mermaid
graph TD
    %% --- STYLES ---
    classDef control fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef infra fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef logic fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef external fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- INPUT ---
    Queue[("URL Queue")] --> FleetMgr{"Fleet Manager"}:::control

    %% --- INFRASTRUCTURE CONFIG ---
    subgraph StealthConfig ["Stealth Configuration"]
        FleetMgr --"Assign IP"--> Proxy["Residential Proxy Pool"]:::infra
        FleetMgr --"Spoof Headers"--> UA["User-Agent Rotator<br/>(iPhone/Chrome/Mac)"]:::infra
        
        Proxy --> Browser
        UA --> Browser
    end

    %% --- THE BROWSER INSTANCE ---
    subgraph BrowserNode ["Headless Browser Instance"]
        Browser["🎭 Playwright Engine<br/>(Stealth Mode)"]:::logic
        Browser --"1. Load Page"--> PageContent["Page DOM / Canvas"]
        
        %% --- DECISION LOGIC ---
        PageContent --> Check{Is Readable?}:::control
        
        %% --- PATH A: STANDARD PARSING ---
        Check --"Yes (Text/HTML)"--> Parser["📄 HTML Parser<br/>(BeautifulSoup)"]:::logic
        
        %% --- PATH B: VISION MODE (The Backup) ---
        Check --"No (Obfuscated/Chart)"--> Screenshot["📸 Take Snapshot"]:::logic
        Screenshot --> VisionLLM["👁️ Vision Model<br/>(GPT-4o / Gemini)"]:::external
        
        %% --- OUTPUT ---
        Parser --> CleanData["✅ Clean JSON"]
        VisionLLM --"OCR / Interpret"--> CleanData
    end
```

### 6.2. Politeness & Rate Limiting
To ensure long-term stability and ethical scraping, Kea implements **Domain-Level Throttling**.

```mermaid
graph LR
    Job[Scrape Job] --> Limiter{Check Limits}
    
    Limiter --"google.com (100 req/min)"--> BucketA[High Capacity Bucket]
    Limiter --"idx.co.id (5 req/min)"--> BucketB[Low Capacity Bucket]
    
    BucketA --> Execute
    BucketB --"Wait 10s"--> Execute
```

---

## ⏳ 7. Asynchronous Task Management

Deep research takes time (minutes to hours). A standard HTTP request will timeout. Kea uses an **Event-Driven Architecture**.

### 7.1. The "Fire-and-Forget" Pattern
1.  **Client:** POST `/api/research/start`
2.  **API:** Returns `202 Accepted` + `job_id`.
3.  **Queue:** Pushes job to **Redis**.
4.  **Worker:** Picks up job, runs for 45 minutes, updates **PostgreSQL** state.
5.  **Client:** Polls `/api/research/status/{job_id}` or receives Webhook.

```mermaid
graph LR
    %% --- STYLES ---
    classDef client fill:#ff7675,stroke:#333,stroke-width:2px,color:#fff;
    classDef api fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef queue fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;
    classDef worker fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    User(("User / Frontend")):::client
    
    subgraph SynchronousLayer ["⚡ Synchronous Layer (Fast)"]
        API["API Gateway<br/>(FastAPI)"]:::api
        Redis[("Redis Task Queue")]:::queue
    end

    subgraph AsyncLayer ["🐢 Asynchronous Layer (Deep Work)"]
        Worker["👷 Background Worker<br/>(Orchestrator Instance)"]:::worker
        Postgres[("PostgreSQL<br/>Job State & History")]:::db
    end

    %% --- STEP 1: THE TRIGGER (FIRE) ---
    User --"1. POST /research/start"--> API
    API --"2. Push Job Payload"--> Redis
    API --"3. Return HTTP 202 Accepted<br/>(Contains: job_id)"--> User

    %% --- STEP 2: THE EXECUTION (FORGET) ---
    Redis -.->|"4. Worker Pops Job"| Worker
    Worker -->|"5. Run Deep Research Loop<br/>(Takes 10-60 mins)"| Worker
    Worker --"6. Update Status: COMPLETED"--> Postgres

    %% --- STEP 3: THE CHECKUP ---
    User -.->|"7. Poll GET /status/{job_id}"| API
    API --"8. Query State"--> Postgres
```
### 7.2. Distributed State Machine
Since the process is long, the state must be persisted. We use **LangGraph Checkpointing**.
*   **Benefit:** If the server crashes at *Step 4 (Analysis)*, it restarts exactly at Step 4, not Step 1.
*   **Pause/Resume:** The system can pause to ask the user for confirmation ("I found a conflict, continue?") and resume days later.

```mermaid
graph TD
    %% --- STYLES ---
    classDef execute fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef save fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef crash fill:#d63031,stroke:#333,stroke-width:2px,color:#fff;
    classDef recover fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- THE THREAD ---
    subgraph ExecutionFlow ["Active Research Thread (ID: 123)"]
        Step1["Step 1: Planner Node"]:::execute --> Save1{"💾 Checkpoint State"}:::save
        Save1 --> Step2["Step 2: Scraper Node"]:::execute
        Step2 --> Save2{"💾 Checkpoint State"}:::save
        
        Save2 --> Crash["🔥 SERVER CRASH / RESTART"]:::crash
    end

    %% --- THE PERSISTENCE LAYER ---
    subgraph StateStore ["PostgreSQL State Store"]
        Postgres[("🐘 DB Table: checkpoints<br/>Key: thread_id_123<br/>Blob: {plan: ..., data: ...}")]:::db
    end

    %% --- THE RECOVERY ---
    subgraph RecoveryFlow ["Recovery / Resume"]
        Restart("🚀 Worker Restart"):::recover --> Load("📂 Load Last Checkpoint<br/>(thread_id_123)"):::recover
        Load --> Resume("▶️ Resume at Step 3: Analysis<br/>(Skip Steps 1 & 2)"):::execute
    end

    %% --- CONNECTIONS ---
    Save1 -.->|Serialize & UPSERT| Postgres
    Save2 -.->|Serialize & UPSERT| Postgres
    Postgres -.->|Deserialize| Load
    Crash -.-> Restart
```

---

## 🚢 8. Deployment Strategy

Kea is designed to be **Infrastructure Agnostic**. It runs on a laptop (Colab/Docker) or a cluster (Kubernetes) using the same code base, controlled by Environment Variables.

### 8.1. The Config Switch
We use a centralized configuration loader that detects the environment.

| Feature | Local / Colab Mode | Production / VPS Mode |
| :--- | :--- | :--- |
| **Database** | SQLite (File) | PostgreSQL (Server) |
| **Queue** | Python `threading` | Redis |
| **Vector DB** | Chroma (Local File) | Qdrant / Weaviate (Server) |
| **Browser** | Local Playwright | Browserless / ScrapingBee |

### 8.2. Production Docker Compose
The system is deployed as a mesh of services.

```yaml
version: '3.8'
services:
  # The Brain
  orchestrator:
    image: kea/orchestrator
    environment:
      - MODE=production
    depends_on: [redis, db]
  
  # The Hands (Isolated for security)
  tool-runner:
    image: kea/sandbox
    command: python -m tools.server
    
  # The State
  redis: {image: "redis:alpine"}
  db: {image: "postgres:15"}
  qdrant: {image: "qdrant/qdrant"}
```

---

## 🔌 9. API Interface (The User Layer)

Kea exposes a RESTful API for integration with frontends, dashboards, or other agents.

### Core Endpoints

#### A. Trigger Research
`POST /v1/research`
```json
{
  "query": "Future of Nickel Mining",
  "depth": "deep",
  "config": {
    "use_memory": true,   // Check Atomic DB first
    "allow_web": true     // Scrape new data
  }
}
```

#### B. The Grand Synthesis (Meta-Analysis)
`POST /v1/synthesis`
```json
{
  "project_id": "session_99",
  "job_ids": ["job_a", "job_b"], // Merge these two
  "mode": "systematic_review"    // or "quantitative_merge"
}
```

#### C. The Shadow Lab (Recalculate)
`POST /v1/tools/recalc`
```json
{
  "artifact_id": "data_job_a.parquet",
  "instruction": "Filter for rows where year > 2023 and recalculate mean revenue."
}
```

---

## 🛡️ 10. Roadmap & Future Proofing

### Phase 1: Foundation (Current)
*   [x] Microservice Architecture.
*   [x] Cyclic Research Graph (OODA Loop).
*   [x] Atomic Fact Memory.

### Phase 2: Perception (Next)
*   [ ] **Multimodal Input:** Allow users to upload a PDF/Image as the start of research.
*   [ ] **Audio Output:** Generate an "Executive Podcast" summary of the research.

### Phase 3: Collaboration (Long Term)
*   [ ] **Swarm Protocol:** Allow multiple "Kea" instances to talk to each other across different servers (e.g., a Finance Kea talking to a Legal Kea).
*   [ ] **Human-in-the-Loop UI:** A dashboard to visualize the "Thought Graph" and manually prune branches.

---

