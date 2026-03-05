---
name: "Clean Architecture Design Reference"
description: "A technical reference for structuring enterprise software systems to ensure separation of concerns and database/framework independence."
domain: "engineering"
tags: ["reference", "architecture", "clean-architecture", "design-patterns", "dependency-injection"]
---

# Standards & Authorities
*   **Primary Source**: *Clean Architecture: A Craftsman's Guide to Software Structure and Design* (Robert C. Martin).
*   **Key Standard**: Dependency Inversion Principle (DIP).
*   **Pattern Reference**: The "Onion" Architecture or Hexagonal Architecture (Ports and Adapters).

## Structural Layout
1.  **Entities (Enterprise Business Rules)**: The most stable part of the code. Contains pure business logic, zero dependencies on external frameworks.
2.  **Use Cases (Application Business Rules)**: Orchestrates the flow of data to and from entities.
3.  **Interface Adapters (Gateways/Controllers)**: Converts data from the format most convenient for the use cases/entities to the format most convenient for external agencies (Web, DB).
4.  **Frameworks & Drivers (External)**: This is where everything else goes: UI, Database, Devices, External APIs.

## The Dependency Rule
Dependencies must only point **INWARDS**. Higher-level layers (Entities/Use Cases) must never know anything about lower-level layers (Database/UI).

## Application in Kea
*   The `KernelCell` represents the "Entity" and "Use Case" layer.
*   The `services/` components are "Adapters" and "Drivers."
*   **MANDATORY**: All state persistence must be abstracted behind an Interface (Repository Pattern) in the Use Case layer, implemented as a DB Client in the Infrastructure layer.
