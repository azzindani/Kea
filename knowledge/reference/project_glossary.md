---
name: "Project Glossary (Enterprise OS Terms)"
description: "Unified semantic definitions for the core components and concepts of the Project ecosystem."
type: "reference"
domain: "corporate"
tags: ["glossary", "ontology", "definitions", "architecture"]
---

# Project Glossary

To ensure absolute semantic alignment across all silicon employees and expert personas, the following definitions are mandated.

## Core Component Definitions
*   **Artifact**: A discrete unit of information (PDF, webscrape, table, fact) stored in the **Vault**. Artifacts are the primary currency of the research swarm.
*   **The Vault**: The high-performance, centralized persistence engine. All cross-service data sharing must occur via the Vault, not the local filesystem.
*   **Silicon Swarm**: The collection of autonomous LLM agents (Personas) working concurrently to solve a complex objective.
*   **Orchestrator**: The "Nervous System" that translates a high-level plan into an executable **DAG**.
*   **MCP Host**: The "Hands" of the system, responsible for spawning and executing tool environments (Just-In-Time).
*   **Liquid Intelligence**: The concept of knowledge being modular, adaptable, and context-injected at runtime, rather than hardcoded.

## Operational Terms
*   **Topological Flow (DAG)**: A Directed Acyclic Graph representing the sequence and dependencies of a research project.
*   **Triangulation**: The process of verifying a single fact across multiple independent and uncorrelated sources.
*   **Cognitive Profile**: A YAML configuration that dictates the specific persona, tool limits, and reasoning style of an agent instance.
*   **Few-Shot CoT**: "Chain of Thought" examples provided to the LLM to demonstrate the desired "Internal Reasoning" before it outputs an answer.
*   **Knowledge Registry**: The semantic database (pgvector) containing all skills, rules, and procedures.

## Governance Terms
*   **Mission Alignment**: The act of verifying that a research path or agent decision maps back to the **Project Corporate Mission**.
*   **Confidence Calibration**: Assigning a numeric reliability score (0.0 to 1.0) to every synthesized finding.
*   **Swarm Conscience**: The set of hard constraints and ethics enforcement overseen by the **Swarm Manager**.
