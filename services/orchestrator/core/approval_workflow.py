"""
Human-in-the-Loop Approval Workflow.

Provides structured approval workflows for enterprise use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Awaitable
from uuid import uuid4

from shared.logging import get_logger

from services.vault.core.audit_trail import AuditEventType, get_audit_trail


logger = get_logger(__name__)


# ============================================================================
# Types
# ============================================================================

class ApprovalType(Enum):
    """Type of approval required."""
    OPTIONAL = "optional"       # Can proceed without approval
    REQUIRED = "required"       # Must wait for approval
    BLOCKING = "blocking"       # Blocks all related work


class ApprovalStatus(Enum):
    """Status of approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalCategory(Enum):
    """Category of approval."""
    DECISION = "decision"           # Decision that needs human input
    DATA_ACCESS = "data_access"     # Access to sensitive data
    EXTERNAL_ACTION = "external"    # External API/action
    COST = "cost"                   # High cost operation
    COMPLIANCE = "compliance"       # Compliance-related
    QUALITY = "quality"             # Quality review
    SECURITY = "security"           # Security-related


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    request_id: str
    category: ApprovalCategory
    approval_type: ApprovalType
    
    # Context
    requester: str          # Agent or system requesting
    work_id: str = ""       # Related work unit
    session_id: str = ""    # Session context
    
    # Details
    title: str = ""
    description: str = ""
    context: dict = field(default_factory=dict)
    options: list[str] = field(default_factory=list)  # Available choices
    
    # Access control
    required_role: str = ""     # Role required to approve
    assignee: str = ""          # Specific assignee (optional)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: datetime | None = None
    expires_at: datetime | None = None
    
    # Result
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: str = ""
    decided_by: str = ""
    decided_at: datetime | None = None
    comments: str = ""
    
    def is_expired(self) -> bool:
        """Check if request is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class WorkflowStep:
    """Single step in approval workflow."""
    step_id: str
    name: str
    required_role: str
    timeout_hours: int = 24
    can_skip: bool = False


@dataclass
class ApprovalWorkflowDefinition:
    """Definition of approval workflow."""
    workflow_id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    
    def add_step(self, role: str, name: str = "", timeout_hours: int = 24):
        """Add step to workflow."""
        step = WorkflowStep(
            step_id=f"step_{len(self.steps) + 1}",
            name=name or f"Approval by {role}",
            required_role=role,
            timeout_hours=timeout_hours,
        )
        self.steps.append(step)


# ============================================================================
# Approval Workflow Manager
# ============================================================================

class ApprovalWorkflow:
    """
    Manages approval workflows.
    
    Features:
    - Multi-step approval chains
    - Role-based access control
    - Timeout and expiration
    - Audit trail integration
    
    Example:
        workflow = ApprovalWorkflow()
        
        # Create request
        request_id = await workflow.create_request(
            category=ApprovalCategory.DECISION,
            title="Approve high-risk operation",
            description="Need approval for external API call",
            required_role="manager",
        )
        
        # Wait for approval
        result = await workflow.wait_for_approval(request_id, timeout_seconds=300)
        
        # Or approve programmatically
        await workflow.approve(request_id, approver="manager@company.com")
    """
    
    def __init__(self):
        self._requests: dict[str, ApprovalRequest] = {}
        self._workflows: dict[str, ApprovalWorkflowDefinition] = {}
        self._callbacks: dict[str, Callable] = {}
        
        # Register default workflows
        self._register_default_workflows()
        
        logger.debug("ApprovalWorkflow initialized")
    
    def _register_default_workflows(self):
        """Register default approval workflows."""
        
        # High-value decision workflow
        high_value = ApprovalWorkflowDefinition(
            "high_value_decision",
            "High Value Decision",
            "Approval chain for high-value decisions",
        )
        high_value.add_step("team_lead", "Team Lead Review")
        high_value.add_step("manager", "Manager Approval")
        self.register_workflow(high_value)
        
        # Compliance workflow
        compliance = ApprovalWorkflowDefinition(
            "compliance_review",
            "Compliance Review",
            "Approval chain for compliance issues",
        )
        compliance.add_step("compliance_officer", "Compliance Officer Review")
        compliance.add_step("legal", "Legal Approval", timeout_hours=48)
        self.register_workflow(compliance)
        
        # Security workflow
        security = ApprovalWorkflowDefinition(
            "security_review",
            "Security Review",
            "Approval chain for security-related actions",
        )
        security.add_step("security_team", "Security Team Review")
        security.add_step("ciso", "CISO Approval")
        self.register_workflow(security)
        
        # Simple approval
        simple = ApprovalWorkflowDefinition(
            "simple",
            "Simple Approval",
            "Single-step approval",
        )
        simple.add_step("approver", "Approval Required")
        self.register_workflow(simple)
    
    def register_workflow(self, workflow: ApprovalWorkflowDefinition):
        """Register approval workflow definition."""
        self._workflows[workflow.workflow_id] = workflow
        logger.debug(f"Registered workflow: {workflow.workflow_id}")
    
    async def create_request(
        self,
        category: ApprovalCategory,
        title: str,
        description: str = "",
        requester: str = "system",
        work_id: str = "",
        context: dict = None,
        options: list[str] = None,
        required_role: str = "",
        assignee: str = "",
        approval_type: ApprovalType = ApprovalType.REQUIRED,
        expires_in_hours: int = 24,
    ) -> str:
        """
        Create approval request.
        
        Returns:
            Request ID
        """
        request = ApprovalRequest(
            request_id=str(uuid4()),
            category=category,
            approval_type=approval_type,
            requester=requester,
            work_id=work_id,
            title=title,
            description=description,
            context=context or {},
            options=options or ["approve", "reject"],
            required_role=required_role,
            assignee=assignee,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
        )
        
        self._requests[request.request_id] = request
        
        # Audit log
        audit = get_audit_trail()
        await audit.log(
            AuditEventType.APPROVAL_REQUESTED,
            action=f"Approval requested: {title}",
            actor=requester,
            details={
                "request_id": request.request_id,
                "category": category.value,
                "required_role": required_role,
            },
        )
        
        logger.info(f"Created approval request: {request.request_id} - {title}")
        
        return request.request_id
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        comments: str = "",
        decision: str = "approved",
    ) -> bool:
        """
        Approve a request.
        
        Returns:
            True if approved successfully
        """
        request = self._requests.get(request_id)
        if not request:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"Request not pending: {request_id}")
            return False
        
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.decision = decision
        request.decided_by = approver
        request.decided_at = datetime.utcnow()
        request.comments = comments
        
        # Audit log
        audit = get_audit_trail()
        await audit.log(
            AuditEventType.APPROVAL_GRANTED,
            action=f"Request approved: {request.title}",
            actor=approver,
            details={
                "request_id": request_id,
                "decision": decision,
                "comments": comments,
            },
        )
        
        # Trigger callback if registered
        if request_id in self._callbacks:
            try:
                await self._callbacks[request_id](request)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
        
        logger.info(f"Approved: {request_id} by {approver}")
        return True
    
    async def reject(
        self,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> bool:
        """
        Reject a request.
        
        Returns:
            True if rejected successfully
        """
        request = self._requests.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.decision = "rejected"
        request.decided_by = approver
        request.decided_at = datetime.utcnow()
        request.comments = reason
        
        # Audit log
        audit = get_audit_trail()
        await audit.log(
            AuditEventType.APPROVAL_DENIED,
            action=f"Request rejected: {request.title}",
            actor=approver,
            details={
                "request_id": request_id,
                "reason": reason,
            },
        )
        
        logger.info(f"Rejected: {request_id} by {approver} - {reason}")
        return True
    
    async def wait_for_approval(
        self,
        request_id: str,
        timeout_seconds: int = 300,
        poll_interval: float = 1.0,
    ) -> ApprovalRequest | None:
        """
        Wait for approval with timeout.
        
        Returns:
            Approved request or None if timeout/rejected
        """
        import asyncio
        
        request = self._requests.get(request_id)
        if not request:
            return None
        
        start_time = datetime.utcnow()
        timeout_delta = timedelta(seconds=timeout_seconds)
        
        while request.status == ApprovalStatus.PENDING:
            if datetime.utcnow() - start_time > timeout_delta:
                logger.warning(f"Approval timeout: {request_id}")
                return None
            
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                return None
            
            await asyncio.sleep(poll_interval)
        
        if request.status == ApprovalStatus.APPROVED:
            return request
        
        return None
    
    def get_pending(
        self,
        role: str = None,
        assignee: str = None,
    ) -> list[ApprovalRequest]:
        """Get pending approval requests."""
        pending = []
        
        for request in self._requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue
            
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                continue
            
            if role and request.required_role and request.required_role != role:
                continue
            
            if assignee and request.assignee and request.assignee != assignee:
                continue
            
            pending.append(request)
        
        return sorted(pending, key=lambda r: r.created_at, reverse=True)
    
    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Get request by ID."""
        return self._requests.get(request_id)
    
    def register_callback(
        self,
        request_id: str,
        callback: Callable[[ApprovalRequest], Awaitable[None]],
    ):
        """Register callback for when request is approved."""
        self._callbacks[request_id] = callback
    
    @property
    def pending_count(self) -> int:
        """Get count of pending requests."""
        return len(self.get_pending())
    
    @property
    def stats(self) -> dict:
        """Get workflow statistics."""
        pending = sum(1 for r in self._requests.values() if r.status == ApprovalStatus.PENDING)
        approved = sum(1 for r in self._requests.values() if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in self._requests.values() if r.status == ApprovalStatus.REJECTED)
        
        return {
            "total": len(self._requests),
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "workflows": len(self._workflows),
        }


# ============================================================================
# HITL Configuration
# ============================================================================

@dataclass
class HITLConfig:
    """
    Configuration for when human intervention is required.
    
    Automatic triggers:
    - Low confidence responses
    - High risk keywords
    - Sensitive domains
    
    Example:
        config = HITLConfig(
            confidence_threshold=0.7,
            high_risk_keywords=["delete", "execute", "transfer"],
        )
        
        if config.requires_review(confidence=0.5, query="delete all files"):
            await request_human_review(...)
    """
    
    # Confidence-based triggers
    confidence_threshold: float = 0.7
    
    # Keyword triggers
    high_risk_keywords: list[str] = field(default_factory=lambda: [
        "delete", "remove", "execute", "transfer", "payment",
        "password", "credential", "sensitive",
    ])
    
    # Domain triggers
    sensitive_domains: list[str] = field(default_factory=lambda: [
        "finance", "legal", "medical", "security", "compliance",
    ])
    
    # Cost thresholds
    cost_threshold: float = 100.0  # Trigger review for operations > $100
    
    # Manual request settings
    allow_user_request: bool = True
    
    def requires_review(
        self,
        confidence: float = 1.0,
        query: str = "",
        domain: str = "",
        cost: float = 0.0,
        user_requested: bool = False,
    ) -> bool:
        """Check if human review is required."""
        
        # User explicitly requested review
        if user_requested and self.allow_user_request:
            return True
        
        # Low confidence
        if confidence < self.confidence_threshold:
            return True
        
        # High risk keywords
        query_lower = query.lower()
        if any(kw in query_lower for kw in self.high_risk_keywords):
            return True
        
        # Sensitive domain
        if domain.lower() in [d.lower() for d in self.sensitive_domains]:
            return True
        
        # Cost threshold
        if cost >= self.cost_threshold:
            return True
        
        return False
    
    def get_trigger_reason(
        self,
        confidence: float = 1.0,
        query: str = "",
        domain: str = "",
        cost: float = 0.0,
    ) -> str | None:
        """Get reason for triggering review."""
        
        if confidence < self.confidence_threshold:
            return f"Low confidence ({confidence:.0%})"
        
        query_lower = query.lower()
        for kw in self.high_risk_keywords:
            if kw in query_lower:
                return f"High risk keyword: {kw}"
        
        if domain.lower() in [d.lower() for d in self.sensitive_domains]:
            return f"Sensitive domain: {domain}"
        
        if cost >= self.cost_threshold:
            return f"High cost: ${cost:.2f}"
        
        return None


# ============================================================================
# Singleton
# ============================================================================

_approval_workflow: ApprovalWorkflow | None = None
_hitl_config: HITLConfig | None = None


def get_approval_workflow() -> ApprovalWorkflow:
    """Get singleton approval workflow."""
    global _approval_workflow
    if _approval_workflow is None:
        _approval_workflow = ApprovalWorkflow()
    return _approval_workflow


def get_hitl_config() -> HITLConfig:
    """Get singleton HITL config."""
    global _hitl_config
    if _hitl_config is None:
        _hitl_config = HITLConfig()
    return _hitl_config


def configure_hitl(config: HITLConfig):
    """Configure HITL settings."""
    global _hitl_config
    _hitl_config = config
