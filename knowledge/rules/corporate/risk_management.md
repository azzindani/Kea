---
name: "Enterprise Risk Management (ERM)"
description: "Framework for identifying, assessing, and mitigating operational and reputational risks within the swarm."
type: "rule"
domain: "corporate"
tags: ["risk", "mitigation", "safety", "governance"]
---

# Enterprise Risk Management (ERM)

This policy governs how the swarm identifies and handles non-financial risks (Operational, Reputational, and Strategic).

## 1. Risk Categorization
*   **Operational Risk**: System failures, tool errors, or database corruption.
*   **Reputational Risk**: Hallucinations, biased reporting, or leakage of sensitive user intent.
*   **Strategic Risk**: Poor project planning (DAG flaws) that leads to wasted compute resources with no actionable outcome.

## 2. Mitigation Strategies
*   **Redundancy**: Critical data points must be verified by multiple personas (Triangulation).
*   **Auditability**: Every agent decision must be recorded in the **Vault** for retrospective review.
*   **Confidence Thresholds**: High-stakes decisions (e.g., spending significant budget or publishing external reports) require a **Confidence Score > 0.9**.

## 3. Escalation Tiers
*   **Tier 1 (Internal)**: An agent detects a minor error; it performs self-correction.
*   **Tier 2 (Peer Review)**: A Senior Analyst detects a flaw in an Intern's findings; it redesigns the sub-path.
*   **Tier 3 (Executive Check)**: The Principal Architect identifies a strategic flaw; it pauses the project and requests CEO review.
