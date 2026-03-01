---
name: "Agent Onboarding Procedure"
description: "The sequence of checks and context-loading steps required when initializing a new agent instance."
type: "procedure"
domain: "corporate"
tags: ["onboarding", "initialization", "bootstrapping", "agent-ops"]
---

# Agent Onboarding Procedure

Every new agent instance spawned by the **Orchestrator** must follow this sequence before attempting its first tool-call.

## 1. Persona Attribution
*   **Identity Check**: Load the assigned **Persona** (Intern, Senior, Principal) from the knowledge base.
*   **Role Immersion**: Review the behavioral profile and "Behavioral Constraints" of the assigned role.

## 2. Governance Loading
*   **Policy Review**: Load the **Swarm Governance Policy** and **Ethics Guidelines**.
*   **Constraint Sync**: Import specific resource limits (Tokens, Time, Parallelism) from the agent's **Cognitive Profile**.

## 3. Mission Contextualization
*   **Mission Sync**: Load the **Project Corporate Mission** to align the agent's internal "Objective Function."
*   **Context Retrieval**: Query the **Vault** for any existing artifacts or task history relevant to the current objective.

## 4. Environment Verification
*   **Heartbeat**: Confirm connectivity to the **Gateway** and **MCP Host**.
*   **Capability Check**: Verify that the required MCP servers (Departments) are online and accessible.

## 5. Ready-to-Work Declaration
*   **Internal Monologue**: Generate a brief "Chain of Thought" summary of the mission, persona, and initial strategy.
*   **Signal**: Send a "Ready" status update to the parent Orchestrator node.
