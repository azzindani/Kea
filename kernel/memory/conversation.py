"""
Conversational Memory Manager.

Provides follow-up detection, smart context injection, and session continuity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class Intent(str, Enum):
    """User intent classification."""
    FOLLOW_UP = "follow_up"      # Continue same topic ("What about X?")
    DEEPER = "deeper"            # Go deeper ("More details")
    REVISE = "revise"            # Modify previous ("Recalculate with...")
    NEW_TOPIC = "new_topic"      # Fresh start ("New research on...")
    COMPARE = "compare"          # Cross-reference ("Compare with last...")
    CLARIFY = "clarify"          # Clarification ("What do you mean by...")
    CONFIRM = "confirm"          # Confirmation response ("Yes", "No")


@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent: Intent | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Active conversation session."""
    session_id: str
    topic: str = ""
    domain: str = ""
    turns: list[ConversationTurn] = field(default_factory=list)
    
    # Accumulated context
    facts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    
    # State
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    def add_turn(self, role: str, content: str, intent: Intent | None = None) -> None:
        """Add a turn to conversation."""
        self.turns.append(ConversationTurn(
            role=role,
            content=content,
            intent=intent,
        ))
        self.last_active = datetime.utcnow()
    
    def get_summary(self, max_turns: int = 5) -> str:
        """Get conversation summary."""
        recent = self.turns[-max_turns:]
        lines = []
        for turn in recent:
            prefix = "User" if turn.role == "user" else "Kea"
            lines.append(f"{prefix}: {turn.content[:100]}...")
        return "\n".join(lines)


class IntentDetector:
    """
    Detect user intent from message.
    
    Example:
        detector = IntentDetector()
        intent = detector.detect("What about the Philippines?", session)
        #   Intent.FOLLOW_UP
    """
    
    def __init__(self):
        self._patterns = {
            Intent.DEEPER: [
                "go deeper", "more detail", "elaborate", "explain more",
                "dive deeper", "expand on", "tell me more", "in depth",
            ],
            Intent.REVISE: [
                "recalculate", "redo", "update", "change to", "modify",
                "with different", "instead of", "adjust", "correct",
            ],
            Intent.NEW_TOPIC: [
                "new research", "different topic", "start fresh",
                "forget previous", "new question", "unrelated",
            ],
            Intent.COMPARE: [
                "compare with", "versus previous", "difference from",
                "how does this", "relative to", "compared to last",
            ],
            Intent.CLARIFY: [
                "what do you mean", "can you explain", "i don't understand",
                "what is", "define", "clarify",
            ],
            Intent.CONFIRM: [
                "yes", "no", "proceed", "continue", "stop", "cancel",
                "approved", "agreed", "go ahead",
            ],
            Intent.FOLLOW_UP: [
                "what about", "and the", "also", "how about",
                "what if", "same for", "regarding",
            ],
        }
    
    def detect(
        self,
        message: str,
        session: ConversationSession | None = None,
    ) -> Intent:
        """Detect intent from message."""
        msg_lower = message.lower().strip()
        
        # Check for confirmation first (short messages)
        if len(msg_lower) < 20:
            for pattern in self._patterns[Intent.CONFIRM]:
                if pattern in msg_lower:
                    return Intent.CONFIRM
        
        # Check patterns in priority order
        for intent in [
            Intent.DEEPER,
            Intent.REVISE,
            Intent.NEW_TOPIC,
            Intent.COMPARE,
            Intent.CLARIFY,
            Intent.FOLLOW_UP,
        ]:
            for pattern in self._patterns[intent]:
                if pattern in msg_lower:
                    return intent
        
        # Default logic based on session
        if session and session.turns:
            # If session exists, default to follow-up
            return Intent.FOLLOW_UP
        
        # New conversation
        return Intent.NEW_TOPIC
    
    def requires_confirmation(self, intent: Intent) -> bool:
        """Check if intent requires user confirmation."""
        return intent in (Intent.DEEPER, Intent.REVISE)


class SmartContextBuilder:
    """
    Build efficient context from session.
    
    Injects only relevant information, not entire history.
    """
    
    def __init__(self, max_facts: int = 5, max_turns: int = 3):
        self.max_facts = max_facts
        self.max_turns = max_turns
    
    def build_context(
        self,
        query: str,
        session: ConversationSession,
    ) -> str:
        """Build context string for LLM."""
        parts = []
        
        # Session summary
        if session.topic:
            parts.append(f"Topic: {session.topic}")
        if session.domain:
            parts.append(f"Domain: {session.domain}")
        
        # Recent turns
        if session.turns:
            recent = session.turns[-self.max_turns:]
            turns_summary = []
            for turn in recent:
                prefix = "User" if turn.role == "user" else "Kea"
                turns_summary.append(f"- {prefix}: {turn.content[:80]}...")
            parts.append(f"Recent:\n" + "\n".join(turns_summary))
        
        # Relevant facts (semantic search would be ideal, but text match for now)
        if session.facts:
            relevant = self._filter_relevant(query, session.facts)
            if relevant:
                parts.append(f"Facts:\n" + "\n".join(f"- {f}" for f in relevant))
        
        # Entities
        if session.entities:
            parts.append(f"Entities: {', '.join(session.entities[:5])}")
        
        # Artifacts (just IDs)
        if session.artifacts:
            parts.append(f"Artifacts: {', '.join(session.artifacts[-3:])}")
        
        return "\n\n".join(parts) if parts else ""
    
    def _filter_relevant(self, query: str, facts: list[str]) -> list[str]:
        """Filter facts relevant to query."""
        query_words = set(query.lower().split())
        
        scored = []
        for fact in facts:
            fact_words = set(fact.lower().split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                scored.append((fact, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, _ in scored[:self.max_facts]]


class ConversationManager:
    """
    Manage conversational sessions.
    
    Example:
        manager = ConversationManager()
        
        # Process user message
        response = await manager.process(
            session_id="session_123",
            message="What about the Philippines?",
            llm_callback=my_llm,
        )
        
        # Check if confirmation needed
        if response.needs_confirmation:
            # Show confirmation prompt
            pass
    """
    
    def __init__(self):
        self.sessions: dict[str, ConversationSession] = {}
        self.intent_detector = IntentDetector()
        self.context_builder = SmartContextBuilder()
    
    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get or create conversation session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(session_id=session_id)
        return self.sessions[session_id]
    
    async def process(
        self,
        session_id: str,
        message: str,
        llm_callback: Any = None,
    ) -> "ConversationResponse":
        """Process user message and return response."""
        session = self.get_or_create_session(session_id)
        
        # Detect intent
        intent = self.intent_detector.detect(message, session)
        
        # Add user turn
        session.add_turn("user", message, intent)
        
        # Check if confirmation needed
        if self.intent_detector.requires_confirmation(intent):
            return ConversationResponse(
                session_id=session_id,
                intent=intent,
                needs_confirmation=True,
                confirmation_prompt=self._get_confirmation_prompt(intent, message),
            )
        
        # Handle based on intent
        if intent == Intent.NEW_TOPIC:
            # Clear session context for new topic
            session.facts = []
            session.entities = []
            session.topic = self._extract_topic(message)
        
        # Build context
        context = self.context_builder.build_context(message, session)
        
        # Generate response via LLM (if callback provided)
        response_text = ""
        if llm_callback:
            response_text = await self._call_llm(llm_callback, message, context)
            session.add_turn("assistant", response_text)
        
        return ConversationResponse(
            session_id=session_id,
            intent=intent,
            context=context,
            response=response_text,
        )
    
    def _get_confirmation_prompt(self, intent: Intent, message: str) -> str:
        """Generate confirmation prompt."""
        if intent == Intent.DEEPER:
            return (
                f"Going deeper will require additional research. "
                f"This may take a few minutes. Proceed? [Yes/No]"
            )
        elif intent == Intent.REVISE:
            return (
                f"This will modify previous findings. "
                f"Do you want to proceed with: '{message[:50]}...'? [Yes/No]"
            )
        return "Proceed? [Yes/No]"
    
    def _extract_topic(self, message: str) -> str:
        """Extract topic from message."""
        # Simple extraction - first N words
        words = message.split()[:5]
        return " ".join(words)
    
    async def _call_llm(self, callback: Any, message: str, context: str) -> str:
        """Call LLM with context."""
        import asyncio
        
        prompt = f"{context}\n\nUser: {message}" if context else message
        
        result = callback(prompt)
        if asyncio.iscoroutine(result):
            return await result
        return result


@dataclass
class ConversationResponse:
    """Response from conversation processing."""
    session_id: str
    intent: Intent
    context: str = ""
    response: str = ""
    needs_confirmation: bool = False
    confirmation_prompt: str = ""


# Global instance
_manager: ConversationManager | None = None


def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager."""
    global _manager
    if _manager is None:
        _manager = ConversationManager()
    return _manager
