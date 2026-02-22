# Entity Recognition (NER)

## Overview
A high-speed **Tier 1** cognitive scanner. It looks at raw blocks of text or context, identifies strict nouns/parameters (Names, Paths, IPs, Amounts), and pulls them out so higher tiers don't have to read the exact text stream to find variables.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% TIER 0 SCHEMA IMPORTS
    subgraph sTier0["Tier 0: Standard Definitions"]
        direction LR
        nSchemaObj["Expected Entity Schema (Pydantic BaseModel)"]
        nSchemaResult["EntitySpan Object Tracker"]
    end

    %% Inputs
    subgraph sInput["Incoming Context Container"]
        nRaw["Raw Text Block or Event JSON"]
    end

    %% TIER 1 ENGINE
    subgraph sTier1["Tier 1: Named Entity Recognition"]
        direction TB
        
        nParse["1. Syntactic Parsing (Tokenization)"]
        nGenerate["2. Candidate Span Generation"]
        nValidate["3. Semantic Extraction & Schema Matching"]
        
        nParse --> nGenerate --> nValidate
    end

    %% Output
    subgraph sOutput["Output to Cognitive Engines"]
        nEntities["List of Exact Extracted Entities"]
    end

    %% Routing
    nRaw --> nParse
    nSchemaObj -.->|Passes constraints to| nValidate
    nValidate -.->|Formats exactly to| nSchemaResult
    
    nSchemaResult --> nEntities

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef in fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nSchemaObj,nSchemaResult t0
    class sInput,nRaw in
    class sTier1,nParse,nGenerate,nValidate t1
    class sOutput,nEntities out
```

## Key Mechanisms
1. **Candidate Span Generation**: The system dynamically scans the sentence and chunks it into specific noun phrases before querying semantics. E.g., for "Send an email to John Doe at Acme Corp," it groups `[John Doe]` and `[Acme Corp]` as distinct spans.
2. **Schema Matching**: Unlike old keyword search, Kea's Tier 1 NER uses the exact Pydantic schema requested by a Tier 2 engine. If the `Expected Entity Schema` requires an `IpAddress`, the NER engine mathematically rejects `[Acme Corp]` and only extracts valid IP spans.
