"""
Message Bus — Async Communication Network for Kernel Cells.

Replaces the one-way fire-and-forget delegation with a multi-directional
communication system inspired by how corporate employees actually talk:

    - **Vertical (Up/Down)** — The command chain.
      Child → Parent: CLARIFY, PROGRESS, ESCALATE, PARTIAL, BLOCKED
      Parent → Child: DELEGATE, REDIRECT, FEEDBACK, CANCEL, RESOURCE

    - **Lateral (Peer-to-Peer)** — The hallway conversation.
      Peer ↔ Peer: SHARE, CONSULT, COORDINATE, HANDOFF, CONFLICT

    - **Broadcast (One-to-Many)** — The all-hands memo.
      One → Many: ANNOUNCE, ALERT, UPDATE

Architecture:
    Every active KernelCell registers with the MessageBus on creation.
    Messages are delivered asynchronously via per-cell mailboxes (asyncio.Queue).
    The bus supports topic-based subscriptions for broadcast messages.
    Communication cost is modelled (token budget) to prevent runaway messaging.

Version: 2.0.0 — Part of Kernel Communication Network (Phase 2)
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from shared.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Message Direction & Channel
# ============================================================================


class MessageDirection(str, Enum):
    """Direction of message flow in the hierarchy."""

    UPWARD = "upward"  # Child → Parent
    DOWNWARD = "downward"  # Parent → Child
    LATERAL = "lateral"  # Peer ↔ Peer
    BROADCAST = "broadcast"  # One → Many


class MessageChannel(str, Enum):
    """Communication channel type."""

    # Vertical (command chain)
    CLARIFY = "clarify"  # "I need more information"
    PROGRESS = "progress"  # "I'm 60% done"
    ESCALATE = "escalate"  # "Above my pay grade"
    PARTIAL = "partial"  # "Here's a draft for review"
    BLOCKED = "blocked"  # "I'm stuck on X"
    DELEGATE = "delegate"  # "Here's your task"
    REDIRECT = "redirect"  # "Change direction"
    FEEDBACK = "feedback"  # "Your draft needs X"
    CANCEL = "cancel"  # "Stop working on this"
    RESOURCE = "resource"  # "Here's more info/budget"

    # Lateral (peer-to-peer)
    SHARE = "share"  # "Here's my data"
    CONSULT = "consult"  # "What's your opinion?"
    COORDINATE = "coordinate"  # "Let's align assumptions"
    HANDOFF = "handoff"  # "My part is done, here's yours"
    CONFLICT = "conflict"  # "Our findings disagree"

    # Broadcast
    ANNOUNCE = "announce"  # "New policy"
    ALERT = "alert"  # "Critical finding"
    UPDATE = "update"  # "Context change"

    # Insight propagation (bottom-up discovery)
    INSIGHT = "insight"  # "I discovered something important"


class MessagePriority(str, Enum):
    """How urgently this message should be processed."""

    LOW = "low"  # Process when idle
    NORMAL = "normal"  # Process in order
    HIGH = "high"  # Process soon
    CRITICAL = "critical"  # Process immediately (interrupts work)


# ============================================================================
# Message Model
# ============================================================================


class CellMessage(BaseModel):
    """
    A single message between kernel cells.

    Every message has a sender, receiver, channel, and payload.
    Messages can be responded to, creating a conversation thread.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    thread_id: str = Field(
        default="",
        description="Groups related messages into a conversation thread",
    )

    # Addressing
    sender_id: str = Field(description="Cell ID of the sender")
    receiver_id: str = Field(
        default="",
        description="Cell ID of the receiver (empty for broadcast)",
    )

    # Channel & Direction
    channel: MessageChannel
    direction: MessageDirection
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)

    # Content
    subject: str = Field(default="", description="Brief subject line")
    content: str = Field(description="Message body")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data payload (e.g., partial results, questions)",
    )

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    token_cost: int = Field(
        default=0,
        description="Estimated token cost of this message",
    )
    requires_response: bool = Field(
        default=False,
        description="Sender is waiting for a reply",
    )
    response_to: str = Field(
        default="",
        description="ID of the message this replies to",
    )
    ttl_seconds: float = Field(
        default=60.0,
        description="Time-to-live: how long to wait for delivery",
    )

    # Status
    delivered: bool = Field(default=False)
    read: bool = Field(default=False)

    def reply(
        self,
        sender_id: str,
        content: str,
        channel: MessageChannel | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CellMessage:
        """Create a reply to this message."""
        return CellMessage(
            thread_id=self.thread_id or self.id,
            sender_id=sender_id,
            receiver_id=self.sender_id,
            channel=channel or self.channel,
            direction=_reverse_direction(self.direction),
            content=content,
            payload=payload or {},
            response_to=self.id,
            requires_response=False,
        )


# ============================================================================
# Mailbox — Per-Cell Message Queue
# ============================================================================


class Mailbox:
    """
    Per-cell message queue with priority support.

    Each cell has one mailbox. Messages from all directions arrive here.
    The cell can poll for new messages or await them asynchronously.
    """

    def __init__(self, cell_id: str, max_size: int = 100) -> None:
        self.cell_id = cell_id
        self._queue: asyncio.Queue[CellMessage] = asyncio.Queue(maxsize=max_size)
        self._history: list[CellMessage] = []
        self._pending_responses: dict[str, asyncio.Future[CellMessage]] = {}

    async def deliver(self, message: CellMessage) -> None:
        """Deliver a message to this mailbox."""
        message.delivered = True
        await self._queue.put(message)
        self._history.append(message)

        # If this message is a response to a pending question, resolve the future
        if message.response_to and message.response_to in self._pending_responses:
            future = self._pending_responses.pop(message.response_to)
            if not future.done():
                future.set_result(message)

    async def receive(self, timeout: float = 5.0) -> CellMessage | None:
        """Wait for the next message (with timeout)."""
        try:
            message = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            message.read = True
            return message
        except TimeoutError:
            return None

    def poll(self) -> CellMessage | None:
        """Non-blocking check for new messages."""
        try:
            message = self._queue.get_nowait()
            message.read = True
            return message
        except asyncio.QueueEmpty:
            return None

    def poll_all(self) -> list[CellMessage]:
        """Drain all pending messages (non-blocking)."""
        messages: list[CellMessage] = []
        while True:
            msg = self.poll()
            if msg is None:
                break
            messages.append(msg)
        return messages

    def poll_by_channel(self, channel: MessageChannel) -> list[CellMessage]:
        """Drain messages of a specific channel type."""
        all_msgs = self.poll_all()
        matching = [m for m in all_msgs if m.channel == channel]
        # Put back non-matching messages
        for m in all_msgs:
            if m.channel != channel:
                try:
                    self._queue.put_nowait(m)
                except asyncio.QueueFull:
                    logger.warning(f"Mailbox {self.cell_id} full, dropping message {m.id}")
        return matching

    async def wait_for_response(
        self,
        message_id: str,
        timeout: float = 30.0,
    ) -> CellMessage | None:
        """
        Wait for a specific response to a sent message.

        Used by clarification round-trips: send a CLARIFY message,
        then wait for the parent's response.
        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future[CellMessage] = loop.create_future()
        self._pending_responses[message_id] = future

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except TimeoutError:
            self._pending_responses.pop(message_id, None)
            logger.warning(f"Mailbox {self.cell_id}: Timeout waiting for response to {message_id}")
            return None

    @property
    def pending_count(self) -> int:
        """Number of unread messages."""
        return self._queue.qsize()

    @property
    def history(self) -> list[CellMessage]:
        """All messages delivered to this mailbox."""
        return list(self._history)

    @property
    def has_messages(self) -> bool:
        """Are there unread messages?"""
        return not self._queue.empty()


# ============================================================================
# Topic Subscription — For Broadcasts
# ============================================================================


@dataclass
class TopicSubscription:
    """A cell's subscription to a broadcast topic."""

    cell_id: str
    pattern: str  # e.g., "research.*", "quality.alerts"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def matches(self, topic: str) -> bool:
        """Check if a topic matches this subscription pattern."""
        if self.pattern == "*":
            return True
        if self.pattern.endswith(".*"):
            prefix = self.pattern[:-2]
            return topic.startswith(prefix)
        return self.pattern == topic


# ============================================================================
# Communication Cost Model
# ============================================================================


@dataclass
class CommunicationCost:
    """Cost model for different communication channels."""

    channel: MessageChannel
    base_token_cost: int
    latency_class: str  # "low" | "medium" | "high" | "very_high"
    worth_it_when: str  # Human-readable guidance


_COMMUNICATION_COSTS: dict[MessageChannel, CommunicationCost] = {
    MessageChannel.CLARIFY: CommunicationCost(
        channel=MessageChannel.CLARIFY,
        base_token_cost=150,
        latency_class="low",
        worth_it_when="Ambiguity > 30% — better to ask than guess wrong",
    ),
    MessageChannel.PROGRESS: CommunicationCost(
        channel=MessageChannel.PROGRESS,
        base_token_cost=50,
        latency_class="low",
        worth_it_when="Long-running task (>3 steps) to keep parent informed",
    ),
    MessageChannel.ESCALATE: CommunicationCost(
        channel=MessageChannel.ESCALATE,
        base_token_cost=500,
        latency_class="high",
        worth_it_when="Blocked or quality risk > 50%",
    ),
    MessageChannel.PARTIAL: CommunicationCost(
        channel=MessageChannel.PARTIAL,
        base_token_cost=200,
        latency_class="medium",
        worth_it_when="Interim results that might change parent's direction",
    ),
    MessageChannel.CONSULT: CommunicationCost(
        channel=MessageChannel.CONSULT,
        base_token_cost=300,
        latency_class="medium",
        worth_it_when="Requires domain expertise the sender lacks",
    ),
    MessageChannel.SHARE: CommunicationCost(
        channel=MessageChannel.SHARE,
        base_token_cost=100,
        latency_class="low",
        worth_it_when="Data that a peer is likely to need",
    ),
    MessageChannel.COORDINATE: CommunicationCost(
        channel=MessageChannel.COORDINATE,
        base_token_cost=200,
        latency_class="medium",
        worth_it_when="Overlapping scope or shared assumptions need alignment",
    ),
    MessageChannel.FEEDBACK: CommunicationCost(
        channel=MessageChannel.FEEDBACK,
        base_token_cost=200,
        latency_class="medium",
        worth_it_when="Draft review identified issues to fix",
    ),
    MessageChannel.ALERT: CommunicationCost(
        channel=MessageChannel.ALERT,
        base_token_cost=100,
        latency_class="very_high",
        worth_it_when="Critical info that changes fundamental assumptions",
    ),
}


def get_communication_cost(channel: MessageChannel) -> int:
    """Get the token cost for a communication channel."""
    cost = _COMMUNICATION_COSTS.get(channel)
    return cost.base_token_cost if cost else 100


# ============================================================================
# The Message Bus
# ============================================================================


class MessageBus:
    """
    Central async message bus for all kernel cell communication.

    Every active KernelCell registers with the bus on creation.
    Messages are routed by cell_id (point-to-point) or topic (broadcast).

    Usage::

        bus = get_message_bus()

        # Register cells
        bus.register("cell-abc")
        bus.register("cell-xyz")

        # Send a message
        await bus.send(CellMessage(
            sender_id="cell-abc",
            receiver_id="cell-xyz",
            channel=MessageChannel.CLARIFY,
            direction=MessageDirection.UPWARD,
            content="Do you mean US market or global?",
            requires_response=True,
        ))

        # Receiver checks mailbox
        msg = await bus.receive("cell-xyz")

        # Send a broadcast
        await bus.broadcast(
            sender_id="cell-abc",
            topic="research.findings",
            content="Found critical market data...",
        )
    """

    def __init__(self) -> None:
        self._mailboxes: dict[str, Mailbox] = {}
        self._subscriptions: list[TopicSubscription] = []
        self._message_log: list[CellMessage] = []
        self._parent_map: dict[str, str] = {}  # child_id → parent_id
        self._children_map: dict[str, list[str]] = defaultdict(list)  # parent_id → [child_ids]
        self._peer_groups: dict[str, set[str]] = defaultdict(set)  # group_key → {cell_ids}
        self._total_messages: int = 0
        self._total_token_cost: int = 0

    # ── Registration ─────────────────────────────────────────────────

    def register(
        self,
        cell_id: str,
        parent_id: str = "",
        peer_group: str = "",
    ) -> Mailbox:
        """
        Register a cell with the message bus.

        Args:
            cell_id: Unique cell identifier.
            parent_id: ID of the parent cell (for vertical messaging).
            peer_group: Group key for lateral messaging (e.g., "research_team").

        Returns:
            The cell's Mailbox for receiving messages.
        """
        if cell_id not in self._mailboxes:
            self._mailboxes[cell_id] = Mailbox(cell_id)
            logger.debug(f"MessageBus: registered cell {cell_id}")

        if parent_id:
            self._parent_map[cell_id] = parent_id
            self._children_map[parent_id].append(cell_id)

        if peer_group:
            self._peer_groups[peer_group].add(cell_id)

        return self._mailboxes[cell_id]

    def unregister(self, cell_id: str) -> None:
        """Remove a cell from the bus (cleanup on cell completion)."""
        self._mailboxes.pop(cell_id, None)
        parent = self._parent_map.pop(cell_id, None)
        if parent and cell_id in self._children_map.get(parent, []):
            self._children_map[parent].remove(cell_id)
        # Remove from peer groups
        for group in self._peer_groups.values():
            group.discard(cell_id)

    # ── Point-to-Point Messaging ─────────────────────────────────────

    async def send(self, message: CellMessage) -> bool:
        """
        Send a message to a specific cell.

        Returns True if delivered, False if receiver not found.
        """
        receiver = self._mailboxes.get(message.receiver_id)
        if not receiver:
            logger.warning(
                f"MessageBus: receiver {message.receiver_id} not found (sender={message.sender_id})"
            )
            return False

        # Apply communication cost
        message.token_cost = get_communication_cost(message.channel)
        self._total_token_cost += message.token_cost
        self._total_messages += 1
        self._message_log.append(message)

        await receiver.deliver(message)

        logger.info(
            f"📨 {message.sender_id} → {message.receiver_id} "
            f"[{message.channel.value}] {message.subject or message.content[:50]}"
        )
        return True

    async def send_and_wait(
        self,
        message: CellMessage,
        timeout: float = 30.0,
    ) -> CellMessage | None:
        """
        Send a message and wait for a response (round-trip).

        Used for clarification: send CLARIFY, wait for parent's RESPONSE.

        Args:
            message: The message to send (must have requires_response=True).
            timeout: How long to wait for the response.

        Returns:
            The response message, or None on timeout.
        """
        message.requires_response = True

        sender_mailbox = self._mailboxes.get(message.sender_id)
        if not sender_mailbox:
            logger.warning(f"MessageBus: sender {message.sender_id} not registered")
            return None

        delivered = await self.send(message)
        if not delivered:
            return None

        # Wait for the response on the sender's mailbox
        return await sender_mailbox.wait_for_response(
            message.id,
            timeout=timeout,
        )

    # ── Vertical Messaging (Up/Down) ─────────────────────────────────

    async def send_to_parent(
        self,
        child_id: str,
        channel: MessageChannel,
        content: str,
        subject: str = "",
        payload: dict[str, Any] | None = None,
        requires_response: bool = False,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> CellMessage | None:
        """
        Send a message upward to the parent cell.

        Convenience method for upward communication (CLARIFY, PROGRESS,
        ESCALATE, PARTIAL, BLOCKED).
        """
        parent_id = self._parent_map.get(child_id)
        if not parent_id:
            logger.debug(f"MessageBus: cell {child_id} has no parent")
            return None

        message = CellMessage(
            sender_id=child_id,
            receiver_id=parent_id,
            channel=channel,
            direction=MessageDirection.UPWARD,
            priority=priority,
            subject=subject,
            content=content,
            payload=payload or {},
            requires_response=requires_response,
        )

        if requires_response:
            return await self.send_and_wait(message)
        else:
            await self.send(message)
            return message

    async def send_to_child(
        self,
        parent_id: str,
        child_id: str,
        channel: MessageChannel,
        content: str,
        subject: str = "",
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> None:
        """
        Send a message downward to a child cell.

        Convenience method for downward communication (FEEDBACK,
        REDIRECT, CANCEL, RESOURCE).
        """
        message = CellMessage(
            sender_id=parent_id,
            receiver_id=child_id,
            channel=channel,
            direction=MessageDirection.DOWNWARD,
            priority=priority,
            subject=subject,
            content=content,
            payload=payload or {},
        )
        await self.send(message)

    async def send_to_all_children(
        self,
        parent_id: str,
        channel: MessageChannel,
        content: str,
        subject: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Send a message to all children of a parent cell."""
        children = self._children_map.get(parent_id, [])
        for child_id in children:
            await self.send_to_child(
                parent_id,
                child_id,
                channel,
                content,
                subject,
                payload,
            )

    # ── Lateral Messaging (Peer-to-Peer) ─────────────────────────────

    async def send_to_peer(
        self,
        sender_id: str,
        receiver_id: str,
        channel: MessageChannel,
        content: str,
        subject: str = "",
        payload: dict[str, Any] | None = None,
        requires_response: bool = False,
    ) -> CellMessage | None:
        """
        Send a message to a peer cell.

        Used for CONSULT, SHARE, COORDINATE, HANDOFF.
        """
        message = CellMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            channel=channel,
            direction=MessageDirection.LATERAL,
            subject=subject,
            content=content,
            payload=payload or {},
            requires_response=requires_response,
        )

        if requires_response:
            return await self.send_and_wait(message)
        else:
            await self.send(message)
            return message

    async def share_with_peers(
        self,
        sender_id: str,
        content: str,
        payload: dict[str, Any] | None = None,
        subject: str = "",
    ) -> int:
        """
        Share data with all peers in the same peer group.

        Returns the number of peers who received the message.
        """
        sent_count = 0
        for group_key, members in self._peer_groups.items():
            if sender_id in members:
                for peer_id in members:
                    if peer_id != sender_id:
                        await self.send_to_peer(
                            sender_id=sender_id,
                            receiver_id=peer_id,
                            channel=MessageChannel.SHARE,
                            content=content,
                            subject=subject,
                            payload=payload or {},
                        )
                        sent_count += 1
        return sent_count

    async def consult_peer(
        self,
        sender_id: str,
        peer_id: str,
        question: str,
        context: str = "",
        timeout: float = 30.0,
    ) -> CellMessage | None:
        """
        Send a consultation request to a peer and wait for response.

        This is a full round-trip: ask question → receive expert opinion.
        """
        return await self.send_to_peer(
            sender_id=sender_id,
            receiver_id=peer_id,
            channel=MessageChannel.CONSULT,
            content=question,
            subject="Consultation request",
            payload={"context": context},
            requires_response=True,
        )

    # ── Broadcast Messaging ───────────────────────────────────────────

    def subscribe(self, cell_id: str, topic_pattern: str) -> None:
        """Subscribe a cell to a topic pattern for broadcast messages."""
        self._subscriptions.append(
            TopicSubscription(
                cell_id=cell_id,
                pattern=topic_pattern,
            )
        )
        logger.debug(f"MessageBus: {cell_id} subscribed to '{topic_pattern}'")

    async def broadcast(
        self,
        sender_id: str,
        topic: str,
        content: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """
        Broadcast a message to all cells subscribed to a topic.

        Returns the number of cells that received the message.
        """
        recipients = set()
        for sub in self._subscriptions:
            if sub.matches(topic) and sub.cell_id != sender_id:
                recipients.add(sub.cell_id)

        for cell_id in recipients:
            message = CellMessage(
                sender_id=sender_id,
                receiver_id=cell_id,
                channel=MessageChannel.ALERT
                if priority == MessagePriority.CRITICAL
                else MessageChannel.UPDATE,
                direction=MessageDirection.BROADCAST,
                priority=priority,
                subject=f"[{topic}]",
                content=content,
                payload=payload or {},
            )
            await self.send(message)

        logger.info(f"📢 Broadcast [{topic}] from {sender_id} → {len(recipients)} recipients")
        return len(recipients)

    # ── Receiving ─────────────────────────────────────────────────────

    async def receive(
        self,
        cell_id: str,
        timeout: float = 5.0,
    ) -> CellMessage | None:
        """Receive the next message for a cell."""
        mailbox = self._mailboxes.get(cell_id)
        if not mailbox:
            return None
        return await mailbox.receive(timeout=timeout)

    def poll(self, cell_id: str) -> CellMessage | None:
        """Non-blocking poll for the next message."""
        mailbox = self._mailboxes.get(cell_id)
        if not mailbox:
            return None
        return mailbox.poll()

    def poll_all(self, cell_id: str) -> list[CellMessage]:
        """Drain all pending messages for a cell."""
        mailbox = self._mailboxes.get(cell_id)
        if not mailbox:
            return []
        return mailbox.poll_all()

    # ── Relationship Queries ─────────────────────────────────────────

    def get_parent(self, cell_id: str) -> str | None:
        """Get the parent cell ID."""
        return self._parent_map.get(cell_id)

    def get_children(self, cell_id: str) -> list[str]:
        """Get all child cell IDs."""
        return list(self._children_map.get(cell_id, []))

    def get_peers(self, cell_id: str) -> list[str]:
        """Get all peer cell IDs (cells in the same peer group)."""
        peers: set[str] = set()
        for group_key, members in self._peer_groups.items():
            if cell_id in members:
                peers.update(members - {cell_id})
        return list(peers)

    def get_siblings(self, cell_id: str) -> list[str]:
        """Get all sibling cell IDs (cells with the same parent)."""
        parent = self._parent_map.get(cell_id)
        if not parent:
            return []
        return [c for c in self._children_map.get(parent, []) if c != cell_id]

    # ── Statistics ────────────────────────────────────────────────────

    @property
    def total_messages(self) -> int:
        """Total messages sent through the bus."""
        return self._total_messages

    @property
    def total_token_cost(self) -> int:
        """Total token cost of all communication."""
        return self._total_token_cost

    @property
    def active_cells(self) -> int:
        """Number of registered cells."""
        return len(self._mailboxes)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive message bus statistics."""
        channel_counts: dict[str, int] = defaultdict(int)
        direction_counts: dict[str, int] = defaultdict(int)
        for msg in self._message_log:
            channel_counts[msg.channel.value] += 1
            direction_counts[msg.direction.value] += 1

        return {
            "total_messages": self._total_messages,
            "total_token_cost": self._total_token_cost,
            "active_cells": len(self._mailboxes),
            "registered_cells": list(self._mailboxes.keys()),
            "parent_child_links": len(self._parent_map),
            "peer_groups": {k: list(v) for k, v in self._peer_groups.items()},
            "topic_subscriptions": len(self._subscriptions),
            "messages_by_channel": dict(channel_counts),
            "messages_by_direction": dict(direction_counts),
        }


# ============================================================================
# Clarification Protocol — The Round-Trip Pattern
# ============================================================================


class ClarificationProtocol:
    """
    Implements the clarification round-trip pattern.

    When a child cell encounters ambiguity, it can ask the parent for
    clarification before proceeding. This prevents "wrong direction" work
    that wastes tokens and produces poor output.

    Usage::

        protocol = ClarificationProtocol(bus, child_id="analyst-42")

        # The child asks
        answer = await protocol.ask_parent(
            question="Do you mean US market or global?",
            options=["US only", "Global", "US + EU"],
            context="Task says 'market share' without specifying geography",
        )

        if answer:
            # Parent responded, use their guidance
            geography = answer.content
        else:
            # Timeout — parent didn't respond, use best guess
            geography = "US"  # Default assumption
    """

    def __init__(self, bus: MessageBus, cell_id: str) -> None:
        self.bus = bus
        self.cell_id = cell_id

    async def ask_parent(
        self,
        question: str,
        options: list[str] | None = None,
        context: str = "",
        timeout: float = 15.0,
    ) -> CellMessage | None:
        """
        Ask the parent a clarifying question and wait for response.

        Args:
            question: The question to ask.
            options: Possible answer choices (helps parent respond quickly).
            context: Why this question matters.
            timeout: How long to wait for the response.

        Returns:
            The parent's response, or None on timeout.
        """
        payload: dict[str, Any] = {}
        if options:
            payload["options"] = options
        if context:
            payload["context"] = context

        return await self.bus.send_to_parent(
            child_id=self.cell_id,
            channel=MessageChannel.CLARIFY,
            content=question,
            subject="Clarification needed",
            payload=payload,
            requires_response=True,
            priority=MessagePriority.HIGH,
        )

    async def report_progress(
        self,
        progress_pct: float,
        current_work: str,
        findings_so_far: str = "",
        blockers: list[str] | None = None,
    ) -> None:
        """
        Send a progress update to the parent.

        Non-blocking — doesn't wait for a response.
        """
        await self.bus.send_to_parent(
            child_id=self.cell_id,
            channel=MessageChannel.PROGRESS,
            content=current_work,
            subject=f"Progress: {progress_pct:.0%}",
            payload={
                "progress_pct": progress_pct,
                "findings_so_far": findings_so_far,
                "blockers": blockers or [],
            },
        )

    async def send_partial_results(
        self,
        partial_content: str,
        confidence: float = 0.5,
        needs_feedback: bool = False,
    ) -> CellMessage | None:
        """
        Send partial/draft results to the parent for early feedback.

        If needs_feedback=True, waits for the parent's review.
        """
        return await self.bus.send_to_parent(
            child_id=self.cell_id,
            channel=MessageChannel.PARTIAL,
            content=partial_content,
            subject="Partial results for review",
            payload={
                "confidence": confidence,
                "needs_feedback": needs_feedback,
            },
            requires_response=needs_feedback,
        )

    async def escalate(
        self,
        reason: str,
        context: str = "",
        partial_work: str = "",
    ) -> None:
        """
        Escalate a problem to the parent.

        Used when the cell is stuck, the task is beyond its capability,
        or a critical issue was discovered.
        """
        await self.bus.send_to_parent(
            child_id=self.cell_id,
            channel=MessageChannel.ESCALATE,
            content=reason,
            subject="Escalation",
            payload={
                "context": context,
                "partial_work": partial_work,
            },
            priority=MessagePriority.HIGH,
        )

    async def report_blocked(
        self,
        blocker: str,
        attempted_solutions: list[str] | None = None,
    ) -> CellMessage | None:
        """
        Report that the cell is blocked and needs help.

        Waits for a response since the cell can't continue without help.
        """
        return await self.bus.send_to_parent(
            child_id=self.cell_id,
            channel=MessageChannel.BLOCKED,
            content=blocker,
            subject="Blocked — need assistance",
            payload={
                "attempted_solutions": attempted_solutions or [],
            },
            requires_response=True,
            priority=MessagePriority.HIGH,
        )


# ============================================================================
# Parent Response Protocol
# ============================================================================


class ParentResponseProtocol:
    """
    Implements the parent side of communication protocols.

    When a parent receives a CLARIFY, PARTIAL, or ESCALATE message
    from a child, this protocol helps generate appropriate responses.

    Usage::

        protocol = ParentResponseProtocol(bus, parent_id="manager-01")

        # Process incoming messages from children
        messages = bus.poll_all("manager-01")
        for msg in messages:
            if msg.channel == MessageChannel.CLARIFY:
                await protocol.respond_to_clarification(msg, answer="US market only")
            elif msg.channel == MessageChannel.PARTIAL:
                await protocol.provide_feedback(msg, feedback="Add more quantitative data")
    """

    def __init__(self, bus: MessageBus, cell_id: str) -> None:
        self.bus = bus
        self.cell_id = cell_id

    async def respond_to_clarification(
        self,
        original_message: CellMessage,
        answer: str,
        additional_context: str = "",
    ) -> None:
        """Respond to a child's clarification question."""
        reply = original_message.reply(
            sender_id=self.cell_id,
            content=answer,
            payload={"additional_context": additional_context},
        )
        await self.bus.send(reply)

    async def provide_feedback(
        self,
        original_message: CellMessage,
        feedback: str,
        approved: bool = False,
        specific_issues: list[str] | None = None,
    ) -> None:
        """Provide feedback on a child's partial results."""
        reply = original_message.reply(
            sender_id=self.cell_id,
            content=feedback,
            channel=MessageChannel.FEEDBACK,
            payload={
                "approved": approved,
                "specific_issues": specific_issues or [],
            },
        )
        await self.bus.send(reply)

    async def redirect_child(
        self,
        child_id: str,
        new_direction: str,
        reason: str = "",
    ) -> None:
        """Send a redirect to a child (change in priorities/scope)."""
        await self.bus.send_to_child(
            parent_id=self.cell_id,
            child_id=child_id,
            channel=MessageChannel.REDIRECT,
            content=new_direction,
            subject="Direction change",
            payload={"reason": reason},
            priority=MessagePriority.HIGH,
        )

    async def cancel_child(
        self,
        child_id: str,
        reason: str = "",
    ) -> None:
        """Cancel a child's work."""
        await self.bus.send_to_child(
            parent_id=self.cell_id,
            child_id=child_id,
            channel=MessageChannel.CANCEL,
            content=reason,
            subject="Work cancelled",
            priority=MessagePriority.CRITICAL,
        )

    async def provide_resource(
        self,
        child_id: str,
        resource_type: str,
        resource_data: Any,
    ) -> None:
        """Send additional resources to a child."""
        await self.bus.send_to_child(
            parent_id=self.cell_id,
            child_id=child_id,
            channel=MessageChannel.RESOURCE,
            content=f"Additional {resource_type} provided",
            subject="Resource provided",
            payload={
                "resource_type": resource_type,
                "resource_data": resource_data,
            },
        )


# ============================================================================
# Singleton Access
# ============================================================================


_bus_instance: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """Get the global message bus singleton."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = MessageBus()
    return _bus_instance


def reset_message_bus() -> None:
    """Reset the message bus (for new sessions)."""
    global _bus_instance
    _bus_instance = None


# ============================================================================
# Utility
# ============================================================================


def _reverse_direction(direction: MessageDirection) -> MessageDirection:
    """Reverse the direction for reply messages."""
    if direction == MessageDirection.UPWARD:
        return MessageDirection.DOWNWARD
    if direction == MessageDirection.DOWNWARD:
        return MessageDirection.UPWARD
    return direction
