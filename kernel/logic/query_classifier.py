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


from kernel.logic.signal_bus import emit_signal, SignalType
from shared.embedding.model_manager import get_embedding_provider

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
        User Input   QueryClassifier   
            CASUAL   Direct LLM response (bypass graph)
            UTILITY   Utility handler (translate/summarize)
            KNOWLEDGE   Simple LLM response
            RESEARCH   IntentionRouter (Path A/B/C/D)
            MULTIMODAL   ModalityHandler first
            UNSAFE   Rejection
    
    Example:
        classifier = QueryClassifier()
        result = classifier.classify("Hello, how are you?")
        #   QueryType.CASUAL, bypass_graph=True
        
        result = classifier.classify("Research Tesla's Q4 earnings")
        #   QueryType.RESEARCH, bypass_graph=False
    """
    
    # ========================================================================
    # Pattern Definitions (Lightweight, no ML required)
    # ========================================================================
    
    # Patterns are loaded from config/vocab/query_classifier.yaml
    
    # Defaults (empty lists) - populated in __init__
    CASUAL_PATTERNS = []
    UTILITY_PATTERNS = []
    KNOWLEDGE_PATTERNS = []
    RESEARCH_PATTERNS = []
    UNSAFE_PATTERNS = []
    SYSTEM_PATTERNS = []
    
    # URL pattern for multimodal detection
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # Semantic Examples for Centroids (Phase 1: Hardcoded, Phase 2: Load from Vault)
    SEMANTIC_EXAMPLES = {
        QueryType.CASUAL: [
            "Hello, how are you?", "Good morning", "Thanks for your help", "Hi there", "Bye",
            "nice to meet you", "what's up", "cool", "ok thanks"
        ],
        QueryType.UTILITY: [
            "Translate this to Spanish", "Summarize this text", "Fix the formatting", "What does this mean?", "Make it a bullet list",
            "rewrite this", "convert to json", "explain this code", "tl;dr"
        ],
        QueryType.KNOWLEDGE: [
            "Who is the CEO of Apple?", "What is the capital of France?", "When was Python created?", "How far is the moon?",
            "definition of photosynthesis", "who won the 1994 world cup"
        ],
        QueryType.RESEARCH: [
            "Compare the financials of Tesla and BYD", "Analyze the impact of AI on healthcare", "Find latest news on quantum computing", 
            "Deep dive into battery technology trends", "investigate the market for evs", "report on recent cybersecurity threats"
        ],
        QueryType.UNSAFE: [
            "How to hack a wifi", "Generate a virus", "Steal credit card numbers", "Bypass security", "Kill a process",
            "make a bomb", "illegal drugs"
        ],
        QueryType.SYSTEM: [
            "Clear my history", "Reset settings", "Configure the model", "System status", "Help me",
            "show configuration", "change model"
        ]
    }

    def __init__(self):
        """Initialize classifier."""
        import re
        from shared.vocab import load_vocab
        
        self._url_regex = re.compile(self.URL_PATTERN)
        
        # Load vocab patterns
        vocab = load_vocab("query_classifier")
        patterns = vocab.get("patterns", {})
        
        self.CASUAL_PATTERNS = patterns.get("casual", [])
        self.UTILITY_PATTERNS = patterns.get("utility", [])
        self.KNOWLEDGE_PATTERNS = patterns.get("knowledge", [])
        self.RESEARCH_PATTERNS = patterns.get("research", [])
        self.UNSAFE_PATTERNS = patterns.get("unsafe", [])
        self.SYSTEM_PATTERNS = patterns.get("system", [])
        
        # Embedding provider (lazy loaded)
        self._embedding_provider = None
        self._centroids: dict[str, list[float]] = {}
        
        logger.debug("QueryClassifier initialized with vocab patterns")

    async def _get_provider(self):
        """Get or initialize embedding provider."""
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    async def _ensure_centroids(self):
        """Compute centroids for each query type if not already done."""
        if self._centroids:
            return

        # Try to load from Vault first (Phase 7)
        try:
            from shared.knowledge.retriever import get_knowledge_retriever
            retriever = get_knowledge_retriever()
            
            # Fetch all classifier examples
            # We expect keys like "query_classifier_casual", "query_classifier_research", etc.
            vault_items = await retriever.search_raw(
                query="query_classifier", 
                limit=20, 
                domain="kernel", 
                category="example"
            )
            
            if vault_items:
                logger.info(f"QueryClassifier: Loaded {len(vault_items)} example sets from Vault")
                
                # Map vault items to QueryType
                # Key format: "query_classifier_{type}" (e.g. "query_classifier_casual")
                for item in vault_items:
                    meta = item.get("metadata", {})
                    examples = meta.get("list", [])
                    if not examples:
                        continue
                        
                    # Extract type from tag or name
                    tags = item.get("tags", [])
                    q_type_str = ""
                    for t in tags:
                        if t.startswith("query_classifier_"):
                            q_type_str = t.replace("query_classifier_", "")
                            break
                    
                    if not q_type_str:
                        continue
                        
                    # Find enum
                    try:
                        q_type = QueryType(q_type_str)
                        # Override hardcoded examples
                        self.SEMANTIC_EXAMPLES[q_type] = examples
                    except ValueError:
                        pass
                        
        except Exception as e:
            logger.warning(f"Failed to load examples from Vault: {e}")

        provider = await self._get_provider()
        
        for q_type, examples in self.SEMANTIC_EXAMPLES.items():
            try:
                # Embed all examples
                embeddings = await provider.embed(examples)
                if not embeddings:
                    continue
                
                # Compute centroid (average vector)
                dim = len(embeddings[0])
                centroid = [0.0] * dim
                for emb in embeddings:
                    for i in range(dim):
                        centroid[i] += emb[i]
                
                # Normalize centroid
                count = len(embeddings)
                if count > 0:
                    magnitude = 0.0
                    for i in range(dim):
                        centroid[i] /= count
                        magnitude += centroid[i] ** 2
                    
                    magnitude = magnitude ** 0.5
                    if magnitude > 0:
                        for i in range(dim):
                            centroid[i] /= magnitude
                            
                self._centroids[q_type.value] = centroid
                
            except Exception as e:
                logger.warning(f"Failed to compute centroid for {q_type}: {e}")
        
        logger.info(f"Computed intent centroids for {len(self._centroids)} types")

    def _create_result(
        self, 
        q_type: QueryType, 
        confidence: float, 
        bypass: bool, 
        patterns: list[str], 
        metadata: dict = None,
        extracted_urls: list[str] = None
    ) -> ClassificationResult:
        """Helper to create result and emit signal."""
        # Emit Signal
        try:
            emit_signal(
                SignalType.CLASSIFICATION,
                "QueryClassifier",
                q_type.value,
                confidence,
                patterns=patterns,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.warning(f"Failed to emit classification signal: {e}")

        return ClassificationResult(
            query_type=q_type,
            confidence=confidence,
            bypass_graph=bypass,
            detected_patterns=patterns,
            extracted_urls=extracted_urls or [],
            metadata=metadata or {}
        )
    
    async def classify(
        self, 
        query: str, 
        attachments: list[Any] = None,
        context: dict[str, Any] = None,
    ) -> ClassificationResult:
        """
        Classify a user query.
        
        v2.0: Uses Embedding-based Neural Classification with Heuristic Fallback.
        
        Args:
            query: User's input text
            attachments: Optional file attachments
            context: Optional conversation context
            
        Returns:
            ClassificationResult with type and metadata
        """
        query_lower = query.lower().strip()
        detected = []
        
        # Check for attachments   multimodal
        if attachments:
            return self._create_result(
                QueryType.MULTIMODAL, 
                1.0, 
                False, 
                ["has_attachments"], 
                metadata={"attachment_count": len(attachments)}
            )
        
        # Check for URLs   multimodal
        urls = self._extract_urls(query)
        if urls:
            return self._create_result(
                QueryType.MULTIMODAL,
                0.9,
                False,
                ["contains_urls"],
                metadata={"url_count": len(urls)},
                extracted_urls=urls
            )
        
        # --------------------------------------------------------------------
        # Step 1: Neural Classification (Primary)
        # --------------------------------------------------------------------
        try:
            provider = await self._get_provider()
            await self._ensure_centroids()
            
            # Embed query
            query_emb = await provider.embed_query(query_lower)
            
            # Find best match
            best_score = -1.0
            best_type = None
            scores = {}
            
            for type_val, centroid in self._centroids.items():
                score = self._cosine_similarity(query_emb, centroid)
                scores[type_val] = score
                if score > best_score:
                    best_score = score
                    best_type = type_val
            
            # Calibrate confidence (Platt scaling approximation)
            confidence = self._calibrate_confidence(best_score)
            
            # Threshold for accepting neural result (0.6 is a conservative start)
            if best_score > 0.6 and best_type:
                q_type = QueryType(best_type)
                
                # Heuristic Override: If "unsafe" pattern matches, ALWAYS trigger unsafe
                if self._matches_patterns(query_lower, self.UNSAFE_PATTERNS):
                    return self._create_result(
                        QueryType.UNSAFE,
                        0.99,
                        True,
                        ["unsafe_override"],
                        metadata={"neural_score": best_score}
                    )
                
                # Determine bypass
                bypass = q_type in [QueryType.CASUAL, QueryType.UTILITY, QueryType.UNSAFE, QueryType.SYSTEM]
                if q_type == QueryType.KNOWLEDGE:
                    bypass = True # Simple knowledge usually bypasses graph
                
                detected.append("neural_match")
                
                return self._create_result(
                    q_type,
                    confidence,
                    bypass,
                    detected,
                    metadata={"neural_scores": scores, "top_score": best_score}
                )
                
        except Exception as e:
            logger.warning(f"Neural classification failed: {e}. Falling back to heuristics.")

        # --------------------------------------------------------------------
        # Step 2: Heuristic Fallback (Legacy)
        # --------------------------------------------------------------------
        
        # Check unsafe first (highest priority)
        if self._matches_patterns(query_lower, self.UNSAFE_PATTERNS):
            detected.append("unsafe_content")
            return self._create_result(QueryType.UNSAFE, 0.95, True, detected)
        
        # Check casual (high priority for UX)
        if self._is_casual(query_lower):
            detected.append("casual_conversation")
            return self._create_result(QueryType.CASUAL, 0.9, True, detected)
        
        # Check system commands
        if self._matches_patterns(query_lower, self.SYSTEM_PATTERNS):
            detected.append("system_command")
            return self._create_result(QueryType.SYSTEM, 0.85, True, detected)
        
        # Check utility (translation, summarization, etc.)
        if self._matches_patterns(query_lower, self.UTILITY_PATTERNS):
            detected.append("utility_request")
            return self._create_result(QueryType.UTILITY, 0.85, True, detected)
        
        # Check research (explicit research intent)
        if self._matches_patterns(query_lower, self.RESEARCH_PATTERNS):
            detected.append("research_request")
            return self._create_result(QueryType.RESEARCH, 0.9, False, detected)
        
        # Check simple knowledge
        if self._matches_patterns(query_lower, self.KNOWLEDGE_PATTERNS):
            detected.append("knowledge_question")
            return self._create_result(QueryType.KNOWLEDGE, 0.8, True, detected)
        
        # Default: if query is short, likely casual/knowledge
        # If long or complex, likely research
        if len(query.split()) <= 5:
            return self._create_result(QueryType.KNOWLEDGE, 0.6, True, ["short_query"])
        
        # Default to research for longer queries
        return self._create_result(QueryType.RESEARCH, 0.5, False, ["default_research"])
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two normalized vectors."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        return dot # Assumes normalized vectors
        
    def _calibrate_confidence(self, score: float) -> float:
        """
        Calibrate raw cosine score to probability (Platt scaling approximation).
        
        Sigmoid-like curve:
        0.5 -> 0.3
        0.6 -> 0.5
        0.7 -> 0.8
        0.8 -> 0.95
        """
        # Simple polynomial approximation for now until we have data
        if score < 0.5:
            return 0.3
        if score > 0.9:
            return 0.99
        
        # Linear interp between 0.5 (0.3) and 0.9 (0.99)
        return 0.3 + (score - 0.5) * (0.69 / 0.4)
    
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
    
    def __init__(self):
        from shared.vocab import load_vocab
        vocab = load_vocab("query_classifier")
        handler_config = vocab.get("casual_handler", {})
        self.triggers = handler_config.get("triggers", {})
        self.responses = handler_config.get("responses", {})

    async def handle(self, query: str, context: dict = None) -> str:
        """Generate casual response."""
        query_lower = query.lower()
        
        import random
        
        farewell_triggers = self.triggers.get("farewell", ["bye", "goodbye"])
        thanks_triggers = self.triggers.get("thanks", ["thank", "thanks"])
        
        farewell_responses = self.responses.get("farewells", ["Goodbye!"])
        thanks_responses = self.responses.get("thanks", ["You're welcome!"])
        greeting_responses = self.responses.get("greetings", ["Hello!"])
        
        if any(p in query_lower for p in farewell_triggers):
            return random.choice(farewell_responses)
        
        if any(p in query_lower for p in thanks_triggers):
            return random.choice(thanks_responses)
        
        return random.choice(greeting_responses)


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
                    max_tokens=32768,
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
        
        from shared.vocab import load_vocab
        vocab = load_vocab("query_classifier")
        fallback = vocab.get("utility_handler", {}).get("fallback_response", "I'll help you with that request.")
        return fallback


class UnsafeHandler(BaseHandler):
    """Handle unsafe/blocked content."""
    
    async def handle(self, query: str, context: dict = None) -> str:
        """Return safe rejection message."""
        from shared.vocab import load_vocab
        vocab = load_vocab("query_classifier")
        response = vocab.get("unsafe_handler", {}).get("response", "I can't help with that request.")
        return response


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
    result = await classifier.classify(query, attachments, context)
    
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
