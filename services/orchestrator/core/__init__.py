# Orchestrator Core Package
"""
Core components for the research orchestrator.

- graph: LangGraph state machine for research workflow
- checkpointing: PostgreSQL state persistence
- degradation: Graceful degradation under resource pressure
- recovery: Error recovery with retry and circuit breaker
- prompt_factory: Dynamic system prompt generation
- query_classifier: Casual/utility/research query routing
- modality: Multimodal input/output handling
- compliance: ISO/SOC2/GDPR compliance framework
- audit_trail: Immutable audit logging
- context_cache: Multi-level context caching
- approval_workflow: Human-in-the-loop workflows
"""

from services.orchestrator.core.graph import (
    GraphState,
    compile_research_graph,
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


# v4.0 Kernel Improvements
from services.orchestrator.core.query_classifier import (
    QueryType,
    QueryClassifier,
    ClassificationResult,
    get_classifier,
    classify_and_handle,
)
from services.orchestrator.core.modality import (
    ModalityType,
    ModalityInput,
    ModalityExtractor,
    ModalityProcessor,
    ModalityOutput,
    OutputSocketRegistry,
    get_modality_extractor,
    get_modality_processor,
    get_output_registry,
)
from services.orchestrator.core.modality_security import (
    ModalityValidator,
    URLValidator,
    ValidationResult,
    get_modality_validator,
    get_url_validator,
)
from services.vault.core.audit_trail import (
    AuditEventType,
    AuditEntry,
    AuditTrail,
    get_audit_trail,
    audited,
)
from services.orchestrator.core.context_cache import (
    CacheLevel,
    ContextCache,
    SemanticCache,
    get_context_cache,
    get_semantic_cache,
    configure_cache,
)

from services.orchestrator.core.approval_workflow import (
    ApprovalType,
    ApprovalStatus,
    ApprovalCategory,
    ApprovalRequest,
    ApprovalWorkflow,
    HITLConfig,
    get_approval_workflow,
    get_hitl_config,
    configure_hitl,
)


__all__ = [
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

    # v3.0 Supervisor

    # v4.0 Query Classifier
    "QueryType",
    "QueryClassifier",
    "ClassificationResult",
    "get_classifier",
    "classify_and_handle",
    # v4.0 Modality
    "ModalityType",
    "ModalityInput",
    "ModalityExtractor",
    "ModalityProcessor",
    "ModalityOutput",
    "OutputSocketRegistry",
    "get_modality_extractor",
    "get_modality_processor",
    "get_output_registry",
    # v4.0 Modality Security
    "ModalityValidator",
    "URLValidator",
    "ValidationResult",
    "get_modality_validator",
    "get_url_validator",
    # v4.0 Audit Trail
    "AuditEventType",
    "AuditEntry",
    "AuditTrail",
    "get_audit_trail",
    "audited",
    # v4.0 Context Cache
    "CacheLevel",
    "ContextCache",
    "SemanticCache",
    "get_context_cache",
    "get_semantic_cache",
    "configure_cache",
    # v4.0 Compliance

    # v4.0 Approval Workflow (HITL)
    "ApprovalType",
    "ApprovalStatus",
    "ApprovalCategory",
    "ApprovalRequest",
    "ApprovalWorkflow",
    "HITLConfig",
    "get_approval_workflow",
    "get_hitl_config",
    "configure_hitl",
]
