# 🧠 Kernel I/O (The Circulatory System)

The **Kernel I/O** subsystem manages the movement of information across the Kea organism. It provides a unified communication bus for inter-cell messaging and a standardized way to handle multi-modal data signals.

## 📐 Architecture

I/O is built on a **Message-Centric** philosophy. Information is never "lost" in deep recursion; instead, it is packaged into envelopes and circulated via a multi-directional bus.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Message Bus** | The "Information Highway". Unified event bus for Upward, Downward, and Lateral communication. | `message_bus.py` |
| **Stdio Envelope** | The "Standard Packet". Every interaction (Input/Output/Internal) is wrapped in this Pydantic envelope. | `stdio_envelope.py` |
| **Modality Engine** | The "Sensory Parser". Handles the transformation and validation of Text, Images, and structured JSON. | `modality.py` |
| **Response Formatter** | The "Translator". Converts internal state, artifacts, and logs into clean, human-readable reports. | `response_formatter.py` |
| **Modality Security** | The "Firewall". Inspects cross-modality signals for architectural or security violations. | `modality_security.py` |

---

## ✨ Key Features

### 1. Multi-Directional Message Bus
Kea replaces simple function returns with a corporate-inspired messaging bus:
- **Downward (Delegation)**: Parents sending instructions to children.
- **Upward (Escalation)**: Children sending clarifications or alerts to parents.
- **Lateral (Collaboration)**: Peer-to-peer sharing of discoveries.
- **Broadcast**: System-wide announcements (e.g., "Resource pressure high").

### 2. High-Fidelity `StdioEnvelope`
All communication in the kernel happens via `StdioEnvelope`. This ensures that every message carries:
- **Instruction**: The core task or message text.
- **Context**: Relevant memory/artifact links.
- **Metadata**: Origin, Timestamp, Request ID, and Priority.

### 3. Unified Modality Handling
The `Modality` engine treats all data types as first-class citizens. Whether the LLM receives a raw text fact, a base64-encoded image, or a complex JSON schema, the I/O system ensures consistent parsing and security filtering.

### 4. Response Synthesis
The `ResponseFormatter` is responsible for "Packaging" the cognitive cycle. It gathers intermediate artifacts, reasoning logs, and child results, producing a final output that adheres to the user-requested format (Markdown, JSON, or Raw Text).

---

## 📁 Component Details

### `message_bus.py`
The most critical part of the circulatory system. It implements `Mailbox` (per-cell queues) and `TopicSubscription` for efficient real-time notification without tight coupling.

### `stdio_envelope.py`
Defines the standard data contract. If a component wants to "talk" to another, it must produce an envelope. This allows for easy tracing, logging, and interception.

### `modality.py`
Handles the complexity of multi-modal streams, ensuring that "Hands" (tools) can return visual data that the "Brain" can perceive.

---
*I/O in Kea provides the connective tissue that allows a collection of independent cells to function as a single, coordinated corporate mind.*
