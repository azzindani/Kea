---
name: "Financial Risk Governance"
description: "Hard constraints on trade sizing, leverage, and asset exposure. Overrides all trading skills."
domain: "governance"
tags: ["risk", "compliance", "safety", "trading"]
type: "rule"
---

# Governance Policy: Risk Management 🛡️

> **"Capital Preservation is the Primary Directive."**

This rule set overrides any "Skill" suggestions. Even if a Technical Analysis skill sees a "perfect setup," these constraints must not be violated.

## 1. Position Sizing
*   **Max Allocation**: No single position shall exceed **5.0%** of the total portfolio equity.
*   **Sector Exposure**: No single sector (e.g., "Tech", "DeFi") shall exceed **25%** of the portfolio.

## 2. Hard Stops
*   **Stop Loss Required**: EVERY trade entry must have a predefined Stop Loss order.
*   **Max Drawdown**: Any strategy hitting a **-10%** daily drawdown must be halted immediately for manual review.

## 3. Prohibited Actions
*   **No Unhedged Leverage**: Margin/Futures trading is forbidden unless explicitly paired with a hedge (e.g., Short Call + Long Stock).
*   **No Penny Stocks**: Assets with a market cap < $50M are blacklisted.
*   **No Naked Options**: Selling options without owning the underlying asset is strictly prohibited.

## Enforcement
The Orchestrator will check every `execute_trade` tool call against these parameters *before* sending it to the execution layer.
