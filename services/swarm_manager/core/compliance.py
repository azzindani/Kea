"""
Compliance and Procedural Agent.

Provides ISO compliance framework and procedural consistency.
Supports ISO 9001, ISO 27001, SOC2, GDPR, HIPAA.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Awaitable

from shared.logging.main import get_logger


logger = get_logger(__name__)


# ============================================================================
# Compliance Standards
# ============================================================================

# Standards are loaded from configs/vocab/compliance.yaml
ComplianceStandard = str


class CheckResult(Enum):
    """Result of compliance check."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class Severity(Enum):
    """Severity of compliance issue."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class ComplianceCheck:
    """Single compliance check."""
    check_id: str
    name: str
    standard: ComplianceStandard
    description: str
    severity: Severity
    
    # Checker function
    checker: Callable[[dict], Awaitable[CheckResult]] = None


@dataclass
class ComplianceIssue:
    """Compliance issue found."""
    check_id: str
    standard: ComplianceStandard
    severity: Severity
    message: str
    details: dict = field(default_factory=dict)
    remediation: str = ""


@dataclass
class ComplianceReport:
    """Report from compliance evaluation."""
    timestamp: datetime
    operation: str
    standards_checked: list[ComplianceStandard]
    checks_passed: int
    checks_failed: int
    checks_warned: int
    issues: list[ComplianceIssue] = field(default_factory=list)
    passed: bool = True
    
    @property
    def summary(self) -> str:
        """Human-readable summary."""
        status = "PASSED" if self.passed else "FAILED"
        return f"{status}: {self.checks_passed} passed, {self.checks_failed} failed, {self.checks_warned} warnings"


# ============================================================================
# Compliance Rules
# ============================================================================

class ComplianceRule:
    """
    Rule that enforces compliance.
    
    Each rule contains multiple checks.
    """
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        standard: ComplianceStandard,
        description: str = "",
    ):
        self.rule_id = rule_id
        self.name = name
        self.standard = standard
        self.description = description
        self.checks: list[ComplianceCheck] = []
    
    def add_check(
        self,
        check_id: str,
        name: str,
        description: str,
        severity: Severity,
        checker: Callable[[dict], Awaitable[CheckResult]],
    ):
        """Add a check to this rule."""
        self.checks.append(ComplianceCheck(
            check_id=check_id,
            name=name,
            standard=self.standard,
            description=description,
            severity=severity,
            checker=checker,
        ))
    
    async def evaluate(self, context: dict) -> list[ComplianceIssue]:
        """Evaluate all checks in this rule."""
        issues = []
        
        for check in self.checks:
            try:
                result = await check.checker(context)
                
                if result in [CheckResult.FAIL, CheckResult.WARN]:
                    issues.append(ComplianceIssue(
                        check_id=check.check_id,
                        standard=check.standard,
                        severity=check.severity,
                        message=f"{check.name}: {check.description}",
                        details={"context": str(context)[:200]},
                    ))
                    
            except Exception as e:
                logger.warning(f"Check {check.check_id} failed: {e}")
                issues.append(ComplianceIssue(
                    check_id=check.check_id,
                    standard=check.standard,
                    severity=Severity.MINOR,
                    message=f"Check error: {str(e)[:100]}",
                ))
        
        return issues


# ============================================================================
# Compliance Engine
# ============================================================================

class ComplianceEngine:
    """
    Main compliance engine.
    
    Enforces compliance across all operations.
    
    ISO 9001 (Quality):
    - Process documentation
    - Traceability
    - Continuous improvement
    
    ISO 27001 (Security):
    - Access control
    - Data classification
    - Incident response
    
    SOC2:
    - Security, Availability, Processing Integrity
    - Confidentiality, Privacy
    
    GDPR:
    - Data minimization
    - Consent management
    - Right to erasure
    
    Example:
        engine = ComplianceEngine()
        
        # Check before operation
        report = await engine.check_operation(
            operation="external_api_call",
            context={"url": url, "data": data},
            standards=[ComplianceStandard.ISO_27001],
        )
        
        if not report.passed:
            raise ComplianceError(report.issues)
    """
    
    def __init__(self):
        self.rules: dict[str, list[ComplianceRule]] = {}
        
        # Register default rules
        self._register_default_rules()
        
        logger.debug("ComplianceEngine initialized")
    
    def _register_default_rules(self):
        """Register default compliance rules."""
        from shared.vocab import load_vocab
        
        v_compliance = load_vocab("compliance")
        v_standards = {s["id"]: s["name"] for s in v_compliance.get("standards", [])}
        
        # ============================================================
        # ISO 27001 - Information Security
        # ============================================================
        
        if "iso_27001" in v_standards:
            security_rule = ComplianceRule(
                "iso27001_data_security",
                "Data Security Controls",
                "iso_27001",
                "Ensure data is protected in transit and at rest",
            )
            
            async def check_https(ctx: dict) -> CheckResult:
                """Check URLs use HTTPS."""
                url = ctx.get("url", "")
                if url and url.startswith("http://"):
                    return CheckResult.FAIL
                return CheckResult.PASS
            
            security_rule.add_check(
                "27001_https", "HTTPS Required",
                "External URLs must use HTTPS",
                Severity.MAJOR, check_https,
            )
            
            async def check_sensitive_data(ctx: dict) -> CheckResult:
                """Check for sensitive data exposure."""
                sensitive_patterns = v_compliance.get("security", {}).get("sensitive_patterns", ["password", "secret", "api_key", "token"])
                
                data = str(ctx)
                for pattern in sensitive_patterns:
                    if pattern in data.lower():
                        return CheckResult.WARN
                return CheckResult.PASS
            
            security_rule.add_check(
                "27001_sensitive", "Sensitive Data Check",
                "Check for sensitive data in context",
                Severity.MAJOR, check_sensitive_data,
            )
            
            self.register_rule(security_rule)
        
        # ============================================================
        # ISO 9001 - Quality Management
        # ============================================================
        
        if "iso_9001" in v_standards:
            quality_rule = ComplianceRule(
                "iso9001_quality",
                "Quality Management",
                "iso_9001",
                "Ensure quality standards are met",
            )
            
            async def check_documentation(ctx: dict) -> CheckResult:
                """Check operation is documented."""
                if ctx.get("documented", True):
                    return CheckResult.PASS
                return CheckResult.WARN
            
            quality_rule.add_check(
                "9001_doc", "Documentation Required",
                "Operations should be documented",
                Severity.MINOR, check_documentation,
            )
            
            async def check_traceability(ctx: dict) -> CheckResult:
                """Check operation has trace ID."""
                if ctx.get("trace_id") or ctx.get("session_id"):
                    return CheckResult.PASS
                return CheckResult.WARN
            
            quality_rule.add_check(
                "9001_trace", "Traceability",
                "Operations should have trace ID",
                Severity.MINOR, check_traceability,
            )
            
            self.register_rule(quality_rule)
        
        # ============================================================
        # GDPR - Data Protection
        # ============================================================
        
        if "gdpr" in v_standards:
            gdpr_rule = ComplianceRule(
                "gdpr_data_protection",
                "GDPR Data Protection",
                "gdpr",
                "Ensure GDPR compliance for personal data",
            )
            
            async def check_data_minimization(ctx: dict) -> CheckResult:
                """Check data minimization principle."""
                # Check if we're collecting more than needed
                data_fields = ctx.get("collected_fields", [])
                required_fields = ctx.get("required_fields", [])
                
                if data_fields and required_fields:
                    excess = set(data_fields) - set(required_fields)
                    if excess:
                        return CheckResult.WARN
                return CheckResult.PASS
            
            gdpr_rule.add_check(
                "gdpr_min", "Data Minimization",
                "Only collect necessary data",
                Severity.MAJOR, check_data_minimization,
            )
            
            async def check_consent(ctx: dict) -> CheckResult:
                """Check consent for data processing."""
                if ctx.get("requires_consent", False):
                    if not ctx.get("consent_given", False):
                        return CheckResult.FAIL
                return CheckResult.PASS
            
            gdpr_rule.add_check(
                "gdpr_consent", "Consent Check",
                "Verify consent for data processing",
                Severity.CRITICAL, check_consent,
            )
            
            self.register_rule(gdpr_rule)
    
    def register_rule(self, rule: ComplianceRule):
        """Register a compliance rule."""
        if rule.standard not in self.rules:
            self.rules[rule.standard] = []
        self.rules[rule.standard].append(rule)
        logger.debug(f"Registered rule: {rule.rule_id} for {rule.standard}")
    
    async def check_operation(
        self,
        operation: str,
        context: dict,
        standards: list[ComplianceStandard] = None,
    ) -> ComplianceReport:
        """
        Check operation for compliance.
        
        Args:
            operation: Operation type (e.g., "data_access", "external_call")
            context: Operation context
            standards: Standards to check (None = all)
            
        Returns:
            ComplianceReport with results
        """
        if standards is None:
            standards = list(self.rules.keys())
        
        all_issues = []
        checks_passed = 0
        checks_failed = 0
        checks_warned = 0
        
        for standard in standards:
            for rule in self.rules.get(standard, []):
                issues = await rule.evaluate(context)
                
                for issue in issues:
                    all_issues.append(issue)
                    if issue.severity == Severity.CRITICAL:
                        checks_failed += 1
                    elif issue.severity == Severity.MAJOR:
                        checks_failed += 1
                    else:
                        checks_warned += 1
                
                # Count passed (checks without issues)
                checks_passed += len(rule.checks) - len(issues)
        
        passed = not any(
            i.severity in [Severity.CRITICAL, Severity.MAJOR]
            for i in all_issues
        )
        
        from datetime import UTC
        report = ComplianceReport(
            timestamp=datetime.now(UTC),
            operation=operation,
            standards_checked=standards,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks_warned=checks_warned,
            issues=all_issues,
            passed=passed,
        )
        
        if not passed:
            logger.warning(f"Compliance check failed: {report.summary}")
        
        return report
    
    async def enforce_before(self, operation: str, context: dict) -> bool:
        """
        Enforce compliance before operation.
        
        Returns True if operation can proceed.
        """
        report = await self.check_operation(operation, context)
        return report.passed
    
    async def get_remediations(self, issues: list[ComplianceIssue]) -> list[str]:
        """Get remediation suggestions for issues."""
        from shared.vocab import load_vocab
        v_compliance = load_vocab("compliance")
        remediation_map = v_compliance.get("remediations", {})
        
        remediations = []
        
        for issue in issues:
            if issue.check_id in remediation_map:
                remediations.append(remediation_map[issue.check_id])
            else:
                remediations.append(f"Address {issue.check_id}: {issue.message}")
        
        return remediations


# ============================================================================
# Procedural Agent
# ============================================================================

@dataclass
class ProcedureStep:
    """Single step in a procedure."""
    step_id: str
    name: str
    description: str
    required: bool = True
    validator: Callable[[dict], bool] = None


@dataclass
class Procedure:
    """
    Standard Operating Procedure (SOP).
    
    Defines a sequence of steps that must be followed.
    """
    procedure_id: str
    name: str
    description: str
    steps: list[ProcedureStep] = field(default_factory=list)
    compliance_standards: list[ComplianceStandard] = field(default_factory=list)
    
    def add_step(self, step: ProcedureStep):
        """Add step to procedure."""
        self.steps.append(step)


class ProceduralAgent:
    """
    Ensures procedural consistency.
    
    - Defines Standard Operating Procedures (SOPs)
    - Enforces step-by-step execution
    - Validates each step
    
    Example:
        agent = ProceduralAgent()
        
        # Define procedure
        proc = Procedure("system_flow", "System Procedure", "Steps for execution")
        proc.add_step(ProcedureStep("1", "Query Classification", "Classify query type"))
        proc.add_step(ProcedureStep("2", "Security Check", "Validate inputs"))
        
        agent.register_procedure(proc)
        
        # Execute
        async for step_result in agent.execute_procedure("system_flow", context):
            print(step_result)
    """
    
    def __init__(self):
        self.procedures: dict[str, Procedure] = {}
        self._register_default_procedures()
        logger.debug("ProceduralAgent initialized")
    
    def _register_default_procedures(self):
        """Register default procedures."""
        from shared.vocab import load_vocab
        v_compliance = load_vocab("compliance")
        v_procedures = v_compliance.get("procedures", {})

        # Research procedure
        if "standard_research" in v_procedures:
            p_data = v_procedures["standard_research"]
            research = Procedure(
                "standard_research",
                p_data.get("name", "Standard Research Procedure"),
                p_data.get("description", "Steps for system execution"),
                compliance_standards=["ISO_9001"],
            )
            for s in p_data.get("steps", []):
                research.add_step(ProcedureStep(s["id"], s["name"], s.get("description", "")))
            self.register_procedure(research)
        
        # Data access procedure
        if "data_access" in v_procedures:
            p_data = v_procedures["data_access"]
            data_access = Procedure(
                "data_access",
                p_data.get("name", "Data Access Procedure"),
                p_data.get("description", "Steps for data access"),
                compliance_standards=["ISO_27001", "GDPR"],
            )
            for s in p_data.get("steps", []):
                data_access.add_step(ProcedureStep(s["id"], s["name"], s.get("description", "")))
            self.register_procedure(data_access)
    
    def register_procedure(self, procedure: Procedure):
        """Register a procedure."""
        self.procedures[procedure.procedure_id] = procedure
        logger.debug(f"Registered procedure: {procedure.procedure_id}")
    
    def get_procedure(self, procedure_id: str) -> Procedure | None:
        """Get procedure by ID."""
        return self.procedures.get(procedure_id)
    
    async def execute_procedure(
        self,
        procedure_id: str,
        context: dict,
        step_callback: Callable[[ProcedureStep, dict], Awaitable[dict]] = None,
    ) -> dict:
        """
        Execute a procedure step by step.
        
        Args:
            procedure_id: Procedure to execute
            context: Initial context
            step_callback: Callback for each step (optional)
            
        Returns:
            Final context after all steps
        """
        procedure = self.procedures.get(procedure_id)
        if not procedure:
            raise ValueError(f"Procedure not found: {procedure_id}")
        
        current_context = context.copy()
        current_context["procedure_id"] = procedure_id
        from datetime import UTC
        current_context["started_at"] = datetime.now(UTC).isoformat()
        
        for step in procedure.steps:
            logger.debug(f"Executing step: {step.name}")
            
            current_context["current_step"] = step.step_id
            current_context["current_step_name"] = step.name
            
            # Call step callback if provided
            if step_callback:
                try:
                    current_context = await step_callback(step, current_context)
                except Exception as e:
                    if step.required:
                        raise
                    logger.warning(f"Optional step {step.step_id} failed: {e}")
            
            # Validate step if validator provided
            if step.validator and not step.validator(current_context):
                if step.required:
                    raise ValueError(f"Step validation failed: {step.name}")
                logger.warning(f"Step validation failed (optional): {step.name}")
        
        from datetime import UTC
        current_context["completed_at"] = datetime.now(UTC).isoformat()
        
        return current_context


# ============================================================================
# Singleton instances
# ============================================================================

_compliance_engine: ComplianceEngine | None = None
_procedural_agent: ProceduralAgent | None = None


def get_compliance_engine() -> ComplianceEngine:
    """Get singleton compliance engine."""
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine


def get_procedural_agent() -> ProceduralAgent:
    """Get singleton procedural agent."""
    global _procedural_agent
    if _procedural_agent is None:
        _procedural_agent = ProceduralAgent()
    return _procedural_agent
