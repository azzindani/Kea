# Orchestrator Core Package
"""
Core components for the research orchestrator.

- graph: LangGraph state machine for research workflow
- checkpointing: PostgreSQL state persistence
- degradation: Graceful degradation under resource pressure
- recovery: Error recovery with retry and circuit breaker
- prompt_factory: Dynamic system prompt generation
"""

from services.orchestrator.core.graph import (
    GraphState,
    compile_research_graph,
)
from services.orchestrator.core.checkpointing import (
    CheckpointStore,
    get_checkpoint_store,
)
from services.orchestrator.core.degradation import (
    GracefulDegrader,
    DegradationLevel,
    get_degrader,
    throttled,
)
from services.orchestrator.core.recovery import (
    retry,
    classify_error,
    ErrorType,
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_breaker,
)
from services.orchestrator.core.prompt_factory import (
    Domain,
    TaskType,
    PromptContext,
    PromptFactory,
    GeneratedPrompt,
    get_prompt_factory,
    generate_prompt,
)
from services.orchestrator.core.agent_spawner import (
    AgentSpawner,
    TaskDecomposer,
    SpawnPlan,
    SwarmResult,
    AgentResult,
    SubTask,
    get_spawner,
)
from services.orchestrator.core.conversation import (
    Intent,
    IntentDetector,
    ConversationManager,
    ConversationSession,
    SmartContextBuilder,
    get_conversation_manager,
)
from services.orchestrator.core.curiosity import (
    CuriosityEngine,
    CuriosityQuestion,
    QuestionType,
    Fact,
    get_curiosity_engine,
)

__all__ = [
    # Graph
    "GraphState",
    "compile_research_graph",
    # Checkpointing
    "CheckpointStore",
    "get_checkpoint_store",
    # Degradation
    "GracefulDegrader",
    "DegradationLevel",
    "get_degrader",
    "throttled",
    # Recovery
    "retry",
    "classify_error",
    "ErrorType",
    "CircuitBreaker",
    "CircuitOpenError",
    "get_circuit_breaker",
    # Prompt Factory
    "Domain",
    "TaskType",
    "PromptContext",
    "PromptFactory",
    "GeneratedPrompt",
    "get_prompt_factory",
    "generate_prompt",
    # Agent Spawner
    "AgentSpawner",
    "TaskDecomposer",
    "SpawnPlan",
    "SwarmResult",
    "AgentResult",
    "SubTask",
    "get_spawner",
    # Conversation
    "Intent",
    "IntentDetector",
    "ConversationManager",
    "ConversationSession",
    "SmartContextBuilder",
    "get_conversation_manager",
    # Curiosity Engine
    "CuriosityEngine",
    "CuriosityQuestion",
    "QuestionType",
    "Fact",
    "get_curiosity_engine",
]


