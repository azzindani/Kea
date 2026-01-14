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
from services.orchestrator.core.guards import (
    ResourceGuard,
    RateLimiter,
    get_resource_guard,
)
from services.orchestrator.core.kill_switch import (
    KillSwitch,
    get_kill_switch,
)
# v3.0 Enterprise Kernel
from services.orchestrator.core.organization import (
    Organization,
    Department,
    Team,
    Role,
    RoleType,
    AgentInstance,
    get_organization,
)
from services.orchestrator.core.work_unit import (
    WorkUnit,
    WorkBoard,
    WorkType,
    WorkStatus,
    Priority,
    get_work_board,
)
from services.orchestrator.core.messaging import (
    Message,
    MessageBus,
    MessageType,
    get_message_bus,
)
from services.orchestrator.core.supervisor import (
    Supervisor,
    QualityGate,
    ReviewResult,
    HealthReport,
    Escalation,
    EscalationType,
    get_supervisor,
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
    # Guards (Security)
    "ResourceGuard",
    "RateLimiter",
    "get_resource_guard",
    # Kill Switch (Emergency Controls)
    "KillSwitch",
    "get_kill_switch",
    # v3.0 Organization
    "Organization",
    "Department",
    "Team",
    "Role",
    "RoleType",
    "AgentInstance",
    "get_organization",
    # v3.0 Work Units
    "WorkUnit",
    "WorkBoard",
    "WorkType",
    "WorkStatus",
    "Priority",
    "get_work_board",
    # v3.0 Messaging
    "Message",
    "MessageBus",
    "MessageType",
    "get_message_bus",
    # v3.0 Supervisor
    "Supervisor",
    "QualityGate",
    "ReviewResult",
    "HealthReport",
    "Escalation",
    "EscalationType",
    "get_supervisor",
]


