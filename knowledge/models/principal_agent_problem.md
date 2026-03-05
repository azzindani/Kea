---
name: "The Principal-Agent Problem (Agency Theory)"
description: "A niche economics/organizational model for the conflict of interest that arises when one entity (the Agent) is delegated to act on behalf of another (the Principal) under conditions of asymmetric information."
domain: "economics/organization"
tags: ["model", "economics", "organization", "agency", "incentives"]
---

# Standards & Authorities
*   **Source**: Jensen & Meckling (1976), the foundational paper on Agency Theory.
*   **Focus**: Misaligned incentives, Moral Hazard, and Adverse Selection.

## Core Framework
1.  **Moral Hazard**: The agent takes excessive risk because they don't bear the full consequences of their actions (e.g., An employee spending the company's money on a redundant tool).
2.  **Adverse Selection**: The principal cannot verify the agent's quality or intentions *before* hiring (e.g., A "Junior" agent claiming "Senior" capabilities).
3.  **Information Asymmetry**: The agent always knows more about their own actions and capabilities than the principal does.
4.  **Agency Costs**: The total cost of monitoring the agent + the cost of the agent's self-serving behavior + residual loss.

## Application in Kea
*   **The Swarm Audit**: Every agent in the DAG is an "Agent" of the "Principal" (The User/Tier 8). They ALL have an incentive alignment problem.
*   **Monitoring Mechanisms**: The `Swarm Manager` must act as the "Board of Directors," auditing agent outputs against the Principal's stated mission.
*   **Incentive Design**: Design reward structures (Compute allocation, Priority access) that align the agent's "Self-Interest" with the Principal's "Objective."
*   **Transparency as a Weapon**: Reduce "Information Asymmetry" by making all agent reasoning visible in the `Vault` audit trail.
