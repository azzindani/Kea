"""
Query Classifier.

First-pass classification of user queries before routing.
Routes casual/utility queries directly, research queries to the graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class QueryType(Enum):
    """Classification of user query intent."""
    CASUAL = "casual"           # Greetings, chitchat, thanks
    UTILITY = "utility"         # Translation, summarization, formatting
    KNOWLEDGE = "knowledge"     # Simple Q&A (no tools needed)
    RESEARCH = "research"       # Complex research (needs tools)
    MULTIMODAL = "multimodal"   # Has attachments/URLs
    UNSAFE = "unsafe"           # Blocked content
    SYSTEM = "system"           # System commands, settings


@dataclass
class ClassificationResult:
    """Result of query classification."""
    query_type: QueryType
    confidence: float
    bypass_graph: bool          # True = skip research graph
    detected_patterns: list[str] = field(default_factory=list)
    extracted_urls: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class QueryClassifier:
    """
    Classify queries before routing to appropriate handler.
    
    Flow:
        User Input → QueryClassifier → 
            CASUAL → Direct LLM response (bypass graph)
            UTILITY → Utility handler (translate/summarize)
            KNOWLEDGE → Simple LLM response
            RESEARCH → IntentionRouter (Path A/B/C/D)
            MULTIMODAL → ModalityHandler first
            UNSAFE → Rejection
    
    Example:
        classifier = QueryClassifier()
        result = classifier.classify("Hello, how are you?")
        # → QueryType.CASUAL, bypass_graph=True
        
        result = classifier.classify("Research Tesla's Q4 earnings")
        # → QueryType.RESEARCH, bypass_graph=False
    """
    
    # ========================================================================
    # Pattern Definitions (Lightweight, no ML required)
    # ========================================================================
    
    CASUAL_PATTERNS = [
        # Greetings
        "hello", "hi ", "hi!", "hey ", "hey!", "howdy", "greetings",
        "good morning", "good afternoon", "good evening", "good night",
        # Farewells
        "bye", "goodbye", "see you", "take care", "later",
        # Thanks
        "thank", "thanks", "thx", "appreciate",
        # Acknowledgments
        "ok", "okay", "got it", "understood", "sure", "alright", "yes", "no",
        # Chitchat
        "how are you", "what's up", "how's it going", "nice to meet",
    ]
    
    UTILITY_PATTERNS = [
        # Translation
        "translate", "in english", "in indonesian", "to english", "to indonesian",
        "what does .* mean", "how do you say",
        # Summarization
        "summarize", "summary", "tldr", "tl;dr", "in brief", "briefly",
        "give me the gist", "key points", "main points",
        # Formatting
        "format", "reformat", "convert to", "make it", "rewrite",
        "bullet points", "numbered list", "as a table",
        # Explanation
        "explain", "what is", "what are", "define", "meaning of",
        "eli5", "explain like", "simple terms",
    ]
    
    KNOWLEDGE_PATTERNS = [
        # Simple facts
        "who is", "who was", "when was", "when did", "where is", "where was",
        "how many", "how much", "how old", "how long", "how far",
        "capital of", "population of", "founder of", "ceo of",
    ]
    
    RESEARCH_PATTERNS = [
        # Research keywords
        "research", "analyze", "investigate", "deep dive", "comprehensive",
        "compare", "contrast", "evaluate", "assess", "review",
        # Data-oriented
        "financial", "earnings", "revenue", "market", "stock",
        "statistics", "data on", "trends", "forecast", "predict",
        # Multi-source
        "sources", "evidence", "studies", "papers", "reports",
        "verify", "validate", "fact check", "cross-reference",
    ]
    
    UNSAFE_PATTERNS = [
        # Harmful content
        "how to hack", "how to steal", "how to kill", "how to hurt",
        "illegal", "malware", "exploit", "bypass security",
        # PII extraction attempts
        "social security", "credit card", "password", "ssn",
    ]
    
    SYSTEM_PATTERNS = [
        "settings", "configure", "config", "preferences",
        "help", "commands", "what can you do",
        "clear history", "reset", "start over",
    ]
    
    # URL pattern for multimodal detection
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    def __init__(self):
        """Initialize classifier."""
        import re
        self._url_regex = re.compile(self.URL_PATTERN)
        logger.debug("QueryClassifier initialized")
    
    def classify(
        self, 
        query: str, 
        attachments: list[Any] = None,
        context: dict[str, Any] = None,
    ) -> ClassificationResult:
        """
        Classify a user query.
        
        Args:
            query: User's input text
            attachments: Optional file attachments
            context: Optional conversation context
            
        Returns:
            ClassificationResult with type and metadata
        """
        query_lower = query.lower().strip()
        detected = []
        
        # Check for attachments → multimodal
        if attachments:
            return ClassificationResult(
                query_type=QueryType.MULTIMODAL,
                confidence=1.0,
                bypass_graph=False,
                detected_patterns=["has_attachments"],
                metadata={"attachment_count": len(attachments)},
            )
        
        # Check for URLs → multimodal
        urls = self._extract_urls(query)
        if urls:
            return ClassificationResult(
                query_type=QueryType.MULTIMODAL,
                confidence=0.9,
                bypass_graph=False,
                detected_patterns=["contains_urls"],
                extracted_urls=urls,
                metadata={"url_count": len(urls)},
            )
        
        # Check unsafe first (highest priority)
        if self._matches_patterns(query_lower, self.UNSAFE_PATTERNS):
            detected.append("unsafe_content")
            return ClassificationResult(
                query_type=QueryType.UNSAFE,
                confidence=0.95,
                bypass_graph=True,
                detected_patterns=detected,
            )
        
        # Check casual (high priority for UX)
        if self._is_casual(query_lower):
            detected.append("casual_conversation")
            return ClassificationResult(
                query_type=QueryType.CASUAL,
                confidence=0.9,
                bypass_graph=True,
                detected_patterns=detected,
            )
        
        # Check system commands
        if self._matches_patterns(query_lower, self.SYSTEM_PATTERNS):
            detected.append("system_command")
            return ClassificationResult(
                query_type=QueryType.SYSTEM,
                confidence=0.85,
                bypass_graph=True,
                detected_patterns=detected,
            )
        
        # Check utility (translation, summarization, etc.)
        if self._matches_patterns(query_lower, self.UTILITY_PATTERNS):
            detected.append("utility_request")
            return ClassificationResult(
                query_type=QueryType.UTILITY,
                confidence=0.85,
                bypass_graph=True,
                detected_patterns=detected,
            )
        
        # Check research (explicit research intent)
        if self._matches_patterns(query_lower, self.RESEARCH_PATTERNS):
            detected.append("research_request")
            return ClassificationResult(
                query_type=QueryType.RESEARCH,
                confidence=0.9,
                bypass_graph=False,
                detected_patterns=detected,
            )
        
        # Check simple knowledge
        if self._matches_patterns(query_lower, self.KNOWLEDGE_PATTERNS):
            detected.append("knowledge_question")
            return ClassificationResult(
                query_type=QueryType.KNOWLEDGE,
                confidence=0.8,
                bypass_graph=True,  # Simple Q&A doesn't need graph
                detected_patterns=detected,
            )
        
        # Default: if query is short, likely casual/knowledge
        # If long or complex, likely research
        if len(query.split()) <= 5:
            return ClassificationResult(
                query_type=QueryType.KNOWLEDGE,
                confidence=0.6,
                bypass_graph=True,
                detected_patterns=["short_query"],
            )
        
        # Default to research for longer queries
        return ClassificationResult(
            query_type=QueryType.RESEARCH,
            confidence=0.5,
            bypass_graph=False,
            detected_patterns=["default_research"],
        )
    
    def _extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text."""
        return self._url_regex.findall(text)
    
    def _is_casual(self, query_lower: str) -> bool:
        """Check if query is casual conversation."""
        # Very short queries are often casual
        if len(query_lower) <= 10:
            for pattern in self.CASUAL_PATTERNS[:10]:  # Check greetings first
                if pattern in query_lower:
                    return True
        
        return self._matches_patterns(query_lower, self.CASUAL_PATTERNS)
    
    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern."""
        for pattern in patterns:
            if pattern in text:
                return True
        return False


# ============================================================================
# Handlers for each query type
# ============================================================================

class BaseHandler:
    """Base class for query handlers."""
    
    async def handle(self, query: str, context: dict = None) -> str:
        raise NotImplementedError


class CasualHandler(BaseHandler):
    """Handle casual conversation directly."""
    
    GREETINGS = [
        "Hello! How can I help you today?",
        "Hi there! What would you like to know?",
        "Hey! Ready to help with your questions.",
    ]
    
    FAREWELLS = [
        "Goodbye! Feel free to come back anytime.",
        "Take care! Let me know if you need anything else.",
    ]
    
    THANKS = [
        "You're welcome! Is there anything else I can help with?",
        "Happy to help! Let me know if you have more questions.",
    ]
    
    async def handle(self, query: str, context: dict = None) -> str:
        """Generate casual response."""
        query_lower = query.lower()
        
        import random
        
        if any(p in query_lower for p in ["bye", "goodbye", "see you"]):
            return random.choice(self.FAREWELLS)
        
        if any(p in query_lower for p in ["thank", "thanks", "appreciate"]):
            return random.choice(self.THANKS)
        
        return random.choice(self.GREETINGS)


class UtilityHandler(BaseHandler):
    """Handle utility requests (translate, summarize, etc.)."""
    
    async def handle(self, query: str, context: dict = None) -> str:
        """
        Route to appropriate utility.
        
        In production, this would call:
        - Translation API
        - Summarization model
        - Formatting logic
        """
        # For now, pass through to LLM
        from shared.llm import OpenRouterProvider, LLMConfig
        from shared.llm.provider import LLMMessage, LLMRole
        
        try:
            import os
            if os.getenv("OPENROUTER_API_KEY"):
                provider = OpenRouterProvider()
                from shared.config import get_settings
                config = LLMConfig(
                    model=get_settings().models.default_model,
                    temperature=0.3,
                    max_tokens=2000,
                )
                
                messages = [
                    LLMMessage(
                        role=LLMRole.SYSTEM,
                        content="You are a helpful assistant. Perform the requested task directly and concisely."
                    ),
                    LLMMessage(role=LLMRole.USER, content=query)
                ]
                
                response = await provider.complete(messages, config)
                return response.content
        except Exception as e:
            logger.error(f"Utility handler error: {e}")
        
        return "I'll help you with that request."


class UnsafeHandler(BaseHandler):
    """Handle unsafe/blocked content."""
    
    async def handle(self, query: str, context: dict = None) -> str:
        """Return safe rejection message."""
        return (
            "I can't help with that request. "
            "If you have other questions, I'm happy to assist."
        )


# ============================================================================
# Integration helper
# ============================================================================

_classifier: QueryClassifier | None = None


def get_classifier() -> QueryClassifier:
    """Get singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier


def get_handler(query_type: QueryType) -> BaseHandler:
    """Get handler for query type."""
    handlers = {
        QueryType.CASUAL: CasualHandler(),
        QueryType.UTILITY: UtilityHandler(),
        QueryType.UNSAFE: UnsafeHandler(),
    }
    return handlers.get(query_type, UtilityHandler())


async def classify_and_handle(
    query: str,
    attachments: list = None,
    context: dict = None,
) -> tuple[ClassificationResult, str | None]:
    """
    Classify query and handle if bypass is enabled.
    
    Returns:
        (classification, response) - response is None if needs graph processing
    """
    classifier = get_classifier()
    result = classifier.classify(query, attachments, context)
    
    if result.bypass_graph and result.query_type in [
        QueryType.CASUAL, 
        QueryType.UTILITY, 
        QueryType.UNSAFE,
        QueryType.SYSTEM,
    ]:
        handler = get_handler(result.query_type)
        response = await handler.handle(query, context)
        return result, response
    
    return result, None
