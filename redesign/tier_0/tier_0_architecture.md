# Tier 0: Base Foundation (Shared Standards)

## Overview
Tier 0 forms the bedrock of the entire Kea system, primarily residing within the `shared/` directory. It contains the most general functions, fundamental abstractions, network protocols, configuration parsers, database schemas, and global standards.

**CRITICAL RULE**: Tier 0 MUST NOT import or depend on any component from Tiers 1 through 5. It is completely blind to upper-level cognitive logic.

## Scope & Responsibilities
- **Data Schemas**: Defines Pydantic models for universal data structures.
- **Protocols & ABCs (Interfaces)**: Defines Python `Protocol` or `ABC` interfaces that upper layers must implement, allowing for dependency injection and mocking.
- **Hardware Abstraction**: Detects available resources (GPU, RAM, cores) to enable Adaptive Scalability.
- **Observability**: Houses base loggers (e.g., `structlog` bindings), telemetry, and tracing components.
- **Configurations**: Parses system variables, paths, and API keys.

## Architecture

```mermaid
flowchart TD
    %% T0 Scope
    subgraph sTier0["Tier 0: Base Foundation (`shared/`)"]
        direction TB
        
        %% Components
        nConfig["Configuration Loader"]
        nSchemas["Universal Base Schemas (Pydantic)"]
        nHardware["Hardware & OS Detection"]
        nLogging["Root Observability (Structlog/OTel)"]
        nProtocols["Core Interface Protocols (ABCs)"]
        
        %% Flow Details
        nConfig -.-> nProtocols
        nSchemas -.-> nProtocols
        nHardware -.-> nLogging
    end

    %% T1 Interface
    subgraph sTier1["Tier 1: Core Processing"]
        direction TB
        nT1Core["Kernel Primitives"]
    end
    
    %% Dependency definition
    sTier1 == "Depends Heavily" ==> sTier0
    
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:2px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    
    class sTier0,nConfig,nSchemas,nHardware,nLogging,nProtocols t0
    class sTier1,nT1Core t1
```
