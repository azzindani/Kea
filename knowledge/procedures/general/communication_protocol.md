---
name: "Swarm Communication Protocol"
description: "Standard Operating Procedure for inter-agent communication, handoffs, and feedback loops."
type: "procedure"
domain: "corporate"
tags: ["communication", "handoff", "workflow", "collaboration"]
---

# Swarm Communication Protocol

This procedure defines how agents should interact to ensure a high-signal, low-noise corporate environment.

## 1. The Handoff Pattern
When handing off a task (e.g., from Principal to Senior), the "Brief" must include:
1.  **Objective**: The specific "Definition of Done."
2.  **Constraints**: Time, budget, or tool limits.
3.  **Context**: Links to relevant artifacts in the **Vault**.
4.  **Priority**: (Low | Medium | High | Critical).

## 2. The Upward Report (Status Update)
When reporting back to a "Manager" persona:
1.  **Status**: (Completed | Blocked | In Progress).
2.  **Top Finding**: The single most important piece of information discovered.
3.  **Evidence**: Artifact IDs for the supporting data.
4.  **Bottlenecks**: Anything preventing the next step.

## 3. Peer Review & Consensus
When two expert personas disagree on a finding:
1.  **Evidence Disclosure**: Each persona lists their supporting artifacts.
2.  **Gap Analysis**: Identify where the data disagrees (Is it a date mismatch? A source credibility issue?).
3.  **Third-Party Review**: Escalate to a Principal Architect for the "Tie-Breaking" vote if a resolution isn't reached in 2 iterations.

## 4. Signal vs. Noise
*   **Avoid Fluff**: Do not use "Courtesy Sentences" (e.g., "I hope this finds you well"). Start with the data.
*   **Reference-Rich**: Use `[Artifact: ID]` tags liberally.
*   **Actionable**: Every message should end with a "Proposed Next Step" or a "Request for Decision."
