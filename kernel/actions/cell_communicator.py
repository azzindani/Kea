"""
Cell Communicator   Communication Interface for Kernel Cells.

Bridges the MessageBus into the KernelCell's cognitive cycle. Every
KernelCell owns a CellCommunicator that provides the high-level API
for all inter-cell communication:

    - **Clarification**   Ask parent before guessing wrong
    - **Progress**   Report status on long-running tasks
    - **Consultation**   Ask peers for domain expertise
    - **Sharing**   Push findings to sibling cells
    - **Escalation**   Push unsolvable problems upward
    - **Message Processing**   Handle incoming messages during execution

The communicator also integrates with WorkingMemory: incoming messages
are automatically registered as focus items, and outgoing messages
draw from memory context.

Design principle: communication has a TOKEN COST. The communicator
tracks spending and refuses messages if the budget is exhausted. This
prevents runaway messaging from consuming the entire token budget.

Version: 2.0.0   Part of Kernel Communication Network (Phase 2)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from shared.logging import get_logger

from kernel.io.message_bus import (
    CellMessage,
    ClarificationProtocol,
    MessageBus,
    MessageChannel,
    MessageDirection,
    MessagePriority,
    ParentResponseProtocol,
    get_communication_cost,
    get_message_bus,
)
from kernel.memory.working_memory import (
    FocusItem,
    FocusItemType,
    QuestionTarget,
    WorkingMemory,
)

logger = get_logger(__name__)


# ============================================================================
# Communication Budget
# ============================================================================


class CommunicationBudget:
    """
    Tracks token spending on inter-cell communication.

    Communication is not free   every message consumes tokens from the
    cell's budget. This prevents cells from spending their entire budget
    on chatter instead of actual work.

    Default allocation: 15% of total token budget.
    """

    def __init__(self, total_task_budget: int, comm_pct: float = 0.15) -> None:
        self.total_budget = int(total_task_budget * comm_pct)
        self.spent: int = 0
        self._message_count: int = 0

    def can_afford(self, channel: MessageChannel) -> bool:
        """Check if we have budget for this message."""
        cost = get_communication_cost(channel)
        return (self.spent + cost) <= self.total_budget

    def spend(self, channel: MessageChannel) -> int:
        """Deduct the cost of a message. Returns the cost."""
        cost = get_communication_cost(channel)
        self.spent += cost
        self._message_count += 1
        return cost

    @property
    def remaining(self) -> int:
        """Remaining communication budget."""
        return max(0, self.total_budget - self.spent)

    @property
    def utilization(self) -> float:
        """Fraction of communication budget used (0.0 - 1.0)."""
        if self.total_budget == 0:
            return 0.0
        return self.spent / self.total_budget

    @property
    def message_count(self) -> int:
        """Total messages sent."""
        return self._message_count


# ============================================================================
# Cell Communicator
# ============================================================================


class CellCommunicator:
    """
    High-level communication interface for a single KernelCell.

    Wraps the MessageBus, ClarificationProtocol, and WorkingMemory
    integration into a clean API that the cognitive cycle can use.

    Usage in KernelCell::

        self.comm = CellCommunicator(
            cell_id=self.cell_id,
            memory=self.working_memory,
            total_budget=self.budget.max_tokens,
            parent_id=parent.cell_id if parent else "",
        )

        # During execution, if stuck:
        answer = await self.comm.ask_parent(
            "Do you mean US market or global?",
            options=["US only", "Global"],
        )

        # Share findings with peers:
        await self.comm.share_with_peers("Found key competitor data")

        # Report progress:
        await self.comm.report_progress(0.6, "Gathered financial data")
    """

    def __init__(
        self,
        cell_id: str,
        memory: WorkingMemory,
        total_budget: int = 30_000,
        parent_id: str = "",
        peer_group: str = "",
        bus: MessageBus | None = None,
    ) -> None:
        self.cell_id = cell_id
        self.memory = memory
        self.budget = CommunicationBudget(total_budget)

        self._bus = bus or get_message_bus()
        self._parent_id = parent_id
        self._peer_group = peer_group

        # Register with bus
        self._mailbox = self._bus.register(
            cell_id=cell_id,
            parent_id=parent_id,
            peer_group=peer_group,
        )

        # Sub-protocols
        self._clarify = ClarificationProtocol(self._bus, cell_id)
        self._parent_proto = ParentResponseProtocol(self._bus, cell_id)

        # Tracking
        self._sent_messages: list[CellMessage] = []
        self._received_messages: list[CellMessage] = []
        self._clarifications_asked: int = 0
        self._clarifications_answered: int = 0

    #   Upward Communication (Child   Parent)  

    async def ask_parent(
        self,
        question: str,
        options: list[str] | None = None,
        context: str = "",
        timeout: float = 15.0,
    ) -> str | None:
        """
        Ask the parent a clarifying question and return the answer.

        This is the primary mechanism for preventing "wrong direction"
        work. If the child detects ambiguity, it asks BEFORE guessing.

        Args:
            question: What to ask.
            options: Possible answers (speeds up parent response).
            context: Why this matters.
            timeout: How long to wait.

        Returns:
            The parent's answer as a string, or None on timeout/no parent.
        """
        if not self._parent_id:
            logger.debug(f"Cell {self.cell_id}: No parent to ask")
            return None

        if not self.budget.can_afford(MessageChannel.CLARIFY):
            logger.warning(
                f"Cell {self.cell_id}: Communication budget exhausted, cannot ask clarification"
            )
            return None

        self.budget.spend(MessageChannel.CLARIFY)
        self._clarifications_asked += 1

        # Track in working memory
        self.memory.ask(
            question_id=f"clarify-{self._clarifications_asked}",
            question=question,
            target=QuestionTarget.PARENT,
            context=context,
        )

        response = await self._clarify.ask_parent(
            question=question,
            options=options,
            context=context,
            timeout=timeout,
        )

        if response:
            self._clarifications_answered += 1
            # Record the answer in working memory
            self.memory.answer_question(
                question_id=f"clarify-{self._clarifications_asked}",
                answer=response.content,
            )
            self.memory.store_fact(
                f"clarification-{self._clarifications_asked}",
                f"Parent clarified: {response.content}",
            )
            # Focus on the new information
            self.memory.focus(
                FocusItem(
                    id=f"clarify-answer-{self._clarifications_asked}",
                    item_type=FocusItemType.FACT,
                    content=f"Clarification: {response.content}",
                    source="parent",
                )
            )
            self._received_messages.append(response)
            return response.content

        logger.info(
            f"Cell {self.cell_id}: No response to clarification (will proceed with best guess)"
        )
        return None

    async def report_progress(
        self,
        progress_pct: float,
        current_work: str,
        findings_so_far: str = "",
    ) -> None:
        """
        Report progress to the parent.

        Non-blocking. Used for long-running tasks to keep the parent
        informed and allow course-correction.
        """
        if not self._parent_id:
            return

        if not self.budget.can_afford(MessageChannel.PROGRESS):
            return

        self.budget.spend(MessageChannel.PROGRESS)

        # Include working memory summary as findings
        if not findings_so_far:
            findings_so_far = self.memory.focus_summary

        await self._clarify.report_progress(
            progress_pct=progress_pct,
            current_work=current_work,
            findings_so_far=findings_so_far,
            blockers=[q.question for q in self.memory.blocking_questions],
        )

    async def send_partial_results(
        self,
        content: str,
        confidence: float = 0.5,
        request_feedback: bool = False,
        timeout: float = 15.0,
    ) -> str | None:
        """
        Send partial/draft results to the parent.

        If request_feedback=True, blocks until the parent reviews
        and provides feedback.

        Returns feedback content if requested, None otherwise.
        """
        if not self._parent_id:
            return None

        if not self.budget.can_afford(MessageChannel.PARTIAL):
            return None

        self.budget.spend(MessageChannel.PARTIAL)

        response = await self._clarify.send_partial_results(
            partial_content=content,
            confidence=confidence,
            needs_feedback=request_feedback,
        )

        if response and request_feedback:
            # Record feedback in working memory
            self.memory.focus(
                FocusItem(
                    id=f"feedback-{response.id}",
                    item_type=FocusItemType.OBSERVATION,
                    content=f"Parent feedback: {response.content}",
                    source="parent",
                )
            )
            self._received_messages.append(response)
            return response.content

        return None

    async def escalate(
        self,
        reason: str,
        context: str = "",
    ) -> None:
        """
        Escalate a problem to the parent.

        Used when the cell determines the task is beyond its capability
        or a critical issue was discovered that needs higher authority.
        """
        if not self._parent_id:
            return

        partial_work = self.memory.compress(max_chars=1000)

        await self._clarify.escalate(
            reason=reason,
            context=context,
            partial_work=partial_work,
        )

        # Record the escalation
        self.memory.decide(
            decision_id=f"escalate-{self.cell_id}",
            description=f"Escalated to parent: {reason}",
            rationale=context or "Problem beyond cell capability",
            confidence=0.3,
        )

    async def report_blocked(
        self,
        blocker: str,
        attempted_solutions: list[str] | None = None,
        timeout: float = 15.0,
    ) -> str | None:
        """
        Report that the cell is blocked and wait for help.

        Returns the parent's response content, or None on timeout.
        """
        if not self._parent_id:
            return None

        if not self.budget.can_afford(MessageChannel.BLOCKED):
            return None

        self.budget.spend(MessageChannel.BLOCKED)

        response = await self._clarify.report_blocked(
            blocker=blocker,
            attempted_solutions=attempted_solutions,
        )

        if response:
            self.memory.focus(
                FocusItem(
                    id=f"unblock-{response.id}",
                    item_type=FocusItemType.FACT,
                    content=f"Parent unblocking: {response.content}",
                    source="parent",
                )
            )
            return response.content

        return None

    #   Lateral Communication (Peer-to-Peer)  

    async def consult_peer(
        self,
        peer_id: str,
        question: str,
        context: str = "",
        timeout: float = 20.0,
    ) -> str | None:
        """
        Ask a peer for their expert opinion.

        Round-trip: sends CONSULT, waits for response.

        Returns:
            Peer's response content, or None on timeout.
        """
        if not self.budget.can_afford(MessageChannel.CONSULT):
            logger.warning(f"Cell {self.cell_id}: No budget for peer consultation")
            return None

        self.budget.spend(MessageChannel.CONSULT)

        response = await self._bus.consult_peer(
            sender_id=self.cell_id,
            peer_id=peer_id,
            question=question,
            context=context,
            timeout=timeout,
        )

        if response:
            # Record in memory
            self.memory.focus(
                FocusItem(
                    id=f"consult-{response.id}",
                    item_type=FocusItemType.FACT,
                    content=f"Peer {peer_id}: {response.content}",
                    source=f"peer:{peer_id}",
                )
            )
            self.memory.store_fact(
                f"peer-consult-{peer_id}",
                response.content,
            )
            self._received_messages.append(response)
            return response.content

        return None

    async def share_with_peers(
        self,
        content: str,
        subject: str = "",
        data: dict[str, Any] | None = None,
    ) -> int:
        """
        Share findings with all peer cells.

        Non-blocking. Used to push data that peers might need.

        Returns:
            Number of peers who received the message.
        """
        if not self.budget.can_afford(MessageChannel.SHARE):
            return 0

        self.budget.spend(MessageChannel.SHARE)

        return await self._bus.share_with_peers(
            sender_id=self.cell_id,
            content=content,
            subject=subject,
            payload=data,
        )

    async def share_upward(
        self,
        content: str,
        urgency: str = "normal",
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Push a high-confidence discovery upward to parent.

        Used for insight propagation: when a child discovers something
        important, it pushes it up so the parent can redistribute to
        sibling cells or escalate further.

        Returns:
            True if message was sent, False if budget exhausted.
        """
        if not self._parent_id:
            return False

        # Use ESCALATE budget as proxy for INSIGHT (similar cost)
        if not self.budget.can_afford(MessageChannel.ESCALATE):
            return False

        self.budget.spend(MessageChannel.ESCALATE)

        await self._bus.send(
            sender_id=self.cell_id,
            receiver_id=self._parent_id,
            channel=MessageChannel.INSIGHT,
            direction=MessageDirection.UPWARD,
            content=content,
            subject=f"Insight ({urgency})",
            payload={"urgency": urgency, **(data or {})},
        )

        self.stats["messages_sent"] = self.stats.get("messages_sent", 0) + 1
        return True

    async def coordinate_with_peer(
        self,
        peer_id: str,
        topic: str,
        proposal: str,
    ) -> str | None:
        """
        Coordinate with a peer on shared assumptions or scope.

        Round-trip: sends COORDINATE, waits for peer's alignment response.
        """
        if not self.budget.can_afford(MessageChannel.COORDINATE):
            return None

        self.budget.spend(MessageChannel.COORDINATE)

        response = await self._bus.send_to_peer(
            sender_id=self.cell_id,
            receiver_id=peer_id,
            channel=MessageChannel.COORDINATE,
            content=proposal,
            subject=f"Coordinate: {topic}",
            requires_response=True,
        )

        if response:
            self.memory.store_fact(
                f"coord-{peer_id}-{topic}",
                f"Agreed with {peer_id}: {response.content}",
            )
            return response.content

        return None

    async def handoff_to_peer(
        self,
        peer_id: str,
        work_product: str,
        instructions: str = "",
    ) -> None:
        """
        Hand off completed work to a peer for continuation.

        Used when Phase A is done and Phase B (owned by peer) depends on it.
        """
        await self._bus.send_to_peer(
            sender_id=self.cell_id,
            receiver_id=peer_id,
            channel=MessageChannel.HANDOFF,
            content=work_product,
            subject="Handoff: my work is ready for you",
            payload={"instructions": instructions},
        )

    async def report_conflict(
        self,
        peer_id: str,
        my_finding: str,
        peer_finding: str,
        topic: str,
    ) -> None:
        """
        Report a data conflict with a peer.

        When two cells produce contradictory findings, this escalates
        the conflict so a manager can resolve it.
        """
        # Notify the peer
        await self._bus.send_to_peer(
            sender_id=self.cell_id,
            receiver_id=peer_id,
            channel=MessageChannel.CONFLICT,
            content=f"My finding: {my_finding}\nYour finding: {peer_finding}",
            subject=f"Data conflict on: {topic}",
        )

        # Escalate to parent for resolution
        if self._parent_id:
            await self._bus.send_to_parent(
                child_id=self.cell_id,
                channel=MessageChannel.ESCALATE,
                content=(
                    f"Data conflict with peer {peer_id} on '{topic}'.\n"
                    f"My finding: {my_finding}\n"
                    f"Their finding: {peer_finding}\n"
                    f"Please resolve."
                ),
                subject="Data conflict needs resolution",
                priority=MessagePriority.HIGH,
            )

    #   Parent-Side Communication  

    async def respond_to_child(
        self,
        message: CellMessage,
        answer: str,
        additional_context: str = "",
    ) -> None:
        """Respond to a child's clarification."""
        await self._parent_proto.respond_to_clarification(
            original_message=message,
            answer=answer,
            additional_context=additional_context,
        )

    async def provide_feedback_to_child(
        self,
        message: CellMessage,
        feedback: str,
        approved: bool = False,
        issues: list[str] | None = None,
    ) -> None:
        """Provide feedback on a child's partial results."""
        await self._parent_proto.provide_feedback(
            original_message=message,
            feedback=feedback,
            approved=approved,
            specific_issues=issues,
        )

    async def redirect_child(
        self,
        child_id: str,
        new_direction: str,
        reason: str = "",
    ) -> None:
        """Redirect a child to a new task direction."""
        await self._parent_proto.redirect_child(
            child_id=child_id,
            new_direction=new_direction,
            reason=reason,
        )

    async def cancel_child(self, child_id: str, reason: str = "") -> None:
        """Cancel a child's work."""
        await self._parent_proto.cancel_child(child_id, reason)

    #   Incoming Message Processing  

    async def process_incoming_messages(
        self,
        handler: Callable[[CellMessage], Awaitable[str | None]] | None = None,
    ) -> list[CellMessage]:
        """
        Process all pending incoming messages.

        Drains the mailbox and:
        1. Registers messages as focus items in working memory.
        2. Calls the optional handler for each message.
        3. Automatically responds if the message requires a response
           and the handler provides content.

        Args:
            handler: Optional async callback (msg)   response_content.
                     If None, messages are registered but not auto-responded.

        Returns:
            List of received messages.
        """
        messages = self._mailbox.poll_all()
        if not messages:
            return []

        for msg in messages:
            self._received_messages.append(msg)

            # Register in working memory
            focus_type = _channel_to_focus_type(msg.channel)
            self.memory.focus(
                FocusItem(
                    id=f"msg-{msg.id}",
                    item_type=focus_type,
                    content=f"[{msg.channel.value}] from {msg.sender_id}: {msg.content[:200]}",
                    source=f"cell:{msg.sender_id}",
                )
            )

            logger.info(
                f"  Cell {self.cell_id} received [{msg.channel.value}] "
                f"from {msg.sender_id}: {msg.subject or msg.content[:50]}"
            )

            # Handle the message
            if handler:
                response_content = await handler(msg)
                if response_content and msg.requires_response:
                    reply = msg.reply(
                        sender_id=self.cell_id,
                        content=response_content,
                    )
                    await self._bus.send(reply)

        return messages

    def check_for_redirect(self) -> CellMessage | None:
        """
        Check if a REDIRECT or CANCEL message has been received.

        Called by the cognitive cycle's monitor phase to detect
        mid-execution course corrections from the parent.
        """
        messages = self._mailbox.poll_by_channel(MessageChannel.REDIRECT)
        if messages:
            return messages[-1]  # Latest redirect

        cancels = self._mailbox.poll_by_channel(MessageChannel.CANCEL)
        if cancels:
            return cancels[-1]

        return None

    def check_for_shared_data(self) -> list[CellMessage]:
        """
        Check if peers have shared data.

        Called during execution to incorporate peer findings.
        """
        shares = self._mailbox.poll_by_channel(MessageChannel.SHARE)
        handoffs = self._mailbox.poll_by_channel(MessageChannel.HANDOFF)

        for msg in shares + handoffs:
            self.memory.store_fact(
                f"shared-{msg.sender_id}-{msg.id}",
                msg.content,
            )
            self.memory.focus(
                FocusItem(
                    id=f"shared-{msg.id}",
                    item_type=FocusItemType.FACT,
                    content=f"Peer {msg.sender_id} shared: {msg.content[:200]}",
                    source=f"peer:{msg.sender_id}",
                )
            )

        return shares + handoffs

    #   Cleanup  

    def cleanup(self) -> None:
        """Unregister from the message bus."""
        self._bus.unregister(self.cell_id)

    #   Statistics  

    @property
    def stats(self) -> dict[str, Any]:
        """Communication statistics for this cell."""
        return {
            "cell_id": self.cell_id,
            "messages_sent": len(self._sent_messages),
            "messages_received": len(self._received_messages),
            "clarifications_asked": self._clarifications_asked,
            "clarifications_answered": self._clarifications_answered,
            "comm_budget_total": self.budget.total_budget,
            "comm_budget_spent": self.budget.spent,
            "comm_budget_remaining": self.budget.remaining,
            "comm_budget_utilization": f"{self.budget.utilization:.1%}",
        }


# ============================================================================
# Utilities
# ============================================================================


def _channel_to_focus_type(channel: MessageChannel) -> FocusItemType:
    """Map a message channel to a working memory focus type."""
    mapping = {
        MessageChannel.CLARIFY: FocusItemType.QUESTION,
        MessageChannel.FEEDBACK: FocusItemType.OBSERVATION,
        MessageChannel.REDIRECT: FocusItemType.DECISION,
        MessageChannel.SHARE: FocusItemType.FACT,
        MessageChannel.CONSULT: FocusItemType.QUESTION,
        MessageChannel.HANDOFF: FocusItemType.FACT,
        MessageChannel.CONFLICT: FocusItemType.HYPOTHESIS,
        MessageChannel.ALERT: FocusItemType.OBSERVATION,
        MessageChannel.PROGRESS: FocusItemType.OBSERVATION,
        MessageChannel.PARTIAL: FocusItemType.OBSERVATION,
        MessageChannel.ESCALATE: FocusItemType.SUB_PROBLEM,
    }
    return mapping.get(channel, FocusItemType.OBSERVATION)
