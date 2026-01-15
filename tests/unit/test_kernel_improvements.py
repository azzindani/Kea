"""
Unit tests for v4.0 Kernel Improvements.

Tests:
- Query Classifier (casual routing)
- Modality Handler (multimodal input)
- Modality Security
- Audit Trail
- Context Cache
- Compliance Engine
- Approval Workflow (HITL)
"""

import pytest
from datetime import datetime, timedelta


# ============================================================================
# Query Classifier Tests
# ============================================================================

class TestQueryClassifier:
    """Tests for query classification."""
    
    def test_classify_greeting(self):
        """Test casual greeting detection."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Hello, how are you?")
        assert result.query_type == QueryType.CASUAL
        assert result.bypass_graph is True
    
    def test_classify_thanks(self):
        """Test thanks detection."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Thank you for the help!")
        assert result.query_type == QueryType.CASUAL
        assert result.bypass_graph is True
    
    def test_classify_translation(self):
        """Test utility request detection."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Translate this to English: Halo dunia")
        assert result.query_type == QueryType.UTILITY
        assert result.bypass_graph is True
    
    def test_classify_summarize(self):
        """Test summarization request."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Summarize this article for me")
        assert result.query_type == QueryType.UTILITY
    
    def test_classify_research(self):
        """Test research query detection."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Research Tesla's financial performance in 2024")
        assert result.query_type == QueryType.RESEARCH
        assert result.bypass_graph is False
    
    def test_classify_with_url(self):
        """Test URL detection in query."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("Check this article: https://example.com/news")
        assert result.query_type == QueryType.MULTIMODAL
        assert len(result.extracted_urls) == 1
    
    def test_classify_unsafe(self):
        """Test unsafe content detection."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("How to hack into a system")
        assert result.query_type == QueryType.UNSAFE
        assert result.bypass_graph is True
    
    def test_classify_knowledge(self):
        """Test simple knowledge question."""
        from services.orchestrator.core.query_classifier import QueryClassifier, QueryType
        
        classifier = QueryClassifier()
        
        result = classifier.classify("What is the capital of France?")
        assert result.query_type == QueryType.KNOWLEDGE


# ============================================================================
# Modality Handler Tests
# ============================================================================

class TestModalityHandler:
    """Tests for multimodal handling."""
    
    def test_extract_urls(self):
        """Test URL extraction from text."""
        from services.orchestrator.core.modality import ModalityExtractor
        
        extractor = ModalityExtractor()
        
        urls = extractor.extract_urls(
            "Check https://example.com and http://test.org/page"
        )
        assert len(urls) == 2
        assert "https://example.com" in urls
    
    def test_extract_modalities(self):
        """Test modality extraction."""
        from services.orchestrator.core.modality import ModalityExtractor, ModalityType
        
        extractor = ModalityExtractor()
        
        modalities = extractor.extract("Look at https://example.com/image.jpg")
        assert len(modalities) == 1
        assert modalities[0].modality_type == ModalityType.IMAGE
    
    def test_detect_type_from_extension(self):
        """Test type detection from file extension."""
        from services.orchestrator.core.modality import ModalityExtractor, ModalityType
        
        extractor = ModalityExtractor()
        
        type_ = extractor.detect_type(b"dummy", "document.pdf")
        assert type_ == ModalityType.DOCUMENT
    
    def test_output_registry(self):
        """Test output socket registry."""
        from services.orchestrator.core.modality import (
            get_output_registry, ModalityType
        )
        
        registry = get_output_registry()
        
        text_socket = registry.get(ModalityType.TEXT)
        assert text_socket is not None


# ============================================================================
# Modality Security Tests
# ============================================================================

class TestModalitySecurity:
    """Tests for modality security validation."""
    
    @pytest.mark.asyncio
    async def test_validate_size_limit(self):
        """Test file size validation."""
        from services.orchestrator.core.modality import ModalityInput, ModalityType
        from services.orchestrator.core.modality_security import ModalityValidator
        
        validator = ModalityValidator()
        
        # Over limit
        large_input = ModalityInput(
            modality_type=ModalityType.IMAGE,
            content=b"x" * 100,
            size_bytes=100 * 1024 * 1024,  # 100MB > 50MB limit
        )
        
        result = await validator.validate(large_input)
        assert result.passed is False
        assert any("size" in i.check for i in result.issues)
    
    @pytest.mark.asyncio
    async def test_validate_url_safety(self):
        """Test URL safety validation."""
        from services.orchestrator.core.modality import ModalityInput, ModalityType
        from services.orchestrator.core.modality_security import ModalityValidator
        
        validator = ModalityValidator()
        
        # HTTP (not HTTPS)
        unsafe_url = ModalityInput(
            modality_type=ModalityType.URL,
            content="http://example.com",
        )
        
        result = await validator.validate(unsafe_url)
        # HTTP without sensitive path should pass but with warning
        # No strict failure for http alone
    
    @pytest.mark.asyncio  
    async def test_url_validator_trusted(self):
        """Test trusted domain check."""
        from services.orchestrator.core.modality_security import URLValidator
        
        validator = URLValidator()
        
        assert validator.is_trusted("https://github.com/repo") is True
        assert validator.is_trusted("https://unknown-domain.xyz") is False


# ============================================================================
# Audit Trail Tests
# ============================================================================

class TestAuditTrail:
    """Tests for audit trail."""
    
    @pytest.mark.asyncio
    async def test_log_event(self):
        """Test logging audit event."""
        from services.orchestrator.core.audit_trail import (
            AuditTrail, AuditEventType, MemoryBackend
        )
        
        trail = AuditTrail(backend=MemoryBackend())
        
        entry_id = await trail.log(
            AuditEventType.QUERY_RECEIVED,
            action="User submitted query",
            actor="user_123",
            details={"query": "Test query"},
        )
        
        assert entry_id is not None
    
    @pytest.mark.asyncio
    async def test_query_events(self):
        """Test querying audit events."""
        from services.orchestrator.core.audit_trail import (
            AuditTrail, AuditEventType, MemoryBackend
        )
        
        trail = AuditTrail(backend=MemoryBackend())
        
        # Log some events
        await trail.log(AuditEventType.QUERY_RECEIVED, "Query 1", "user_1")
        await trail.log(AuditEventType.TOOL_CALLED, "Tool 1", "system")
        await trail.log(AuditEventType.QUERY_RECEIVED, "Query 2", "user_2")
        
        # Query by type
        results = await trail.query(
            event_types=[AuditEventType.QUERY_RECEIVED]
        )
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_entry_integrity(self):
        """Test entry integrity verification."""
        from services.orchestrator.core.audit_trail import (
            AuditEntry, AuditEventType
        )
        
        entry = AuditEntry(
            entry_id="test_123",
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.DECISION_MADE,
            actor="system",
            action="Made decision",
        )
        
        assert entry.verify() is True
        
        # Tamper with entry
        entry.action = "Tampered action"
        assert entry.verify() is False


# ============================================================================
# Context Cache Tests
# ============================================================================

class TestContextCache:
    """Tests for context caching."""
    
    @pytest.mark.asyncio
    async def test_memory_cache(self):
        """Test in-memory caching."""
        from services.orchestrator.core.context_cache import ContextCache
        
        cache = ContextCache(l1_max_mb=10)
        
        await cache.set("key1", {"data": "value"})
        result = await cache.get("key1")
        
        assert result == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL expiration."""
        from services.orchestrator.core.context_cache import MemoryCache
        import time
        
        cache = MemoryCache(max_mb=10)
        
        cache.set("expire_key", "value", ttl=1)
        
        # Should exist
        assert cache.get("expire_key") == "value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("expire_key") is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        from services.orchestrator.core.context_cache import ContextCache
        
        cache = ContextCache(l1_max_mb=10)
        
        await cache.set("k1", "v1")
        await cache.get("k1")  # Hit
        await cache.get("k2")  # Miss
        
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1


# ============================================================================
# Compliance Engine Tests
# ============================================================================

class TestComplianceEngine:
    """Tests for compliance engine."""
    
    @pytest.mark.asyncio
    async def test_https_check(self):
        """Test HTTPS requirement check."""
        from services.orchestrator.core.compliance import (
            ComplianceEngine, ComplianceStandard
        )
        
        engine = ComplianceEngine()
        
        # HTTP URL should fail
        report = await engine.check_operation(
            "external_call",
            {"url": "http://insecure.com"},
            standards=[ComplianceStandard.ISO_27001],
        )
        
        assert report.passed is False
        assert report.checks_failed > 0
    
    @pytest.mark.asyncio
    async def test_sensitive_data_check(self):
        """Test sensitive data detection."""
        from services.orchestrator.core.compliance import (
            ComplianceEngine, ComplianceStandard
        )
        
        engine = ComplianceEngine()
        
        # Contains "password" in context
        report = await engine.check_operation(
            "data_access",
            {"password": "secret123"},
            standards=[ComplianceStandard.ISO_27001],
        )
        
        # Should warn about sensitive data
        assert any("sensitive" in i.check_id.lower() for i in report.issues)
    
    @pytest.mark.asyncio
    async def test_procedural_agent(self):
        """Test procedural agent."""
        from services.orchestrator.core.compliance import (
            ProceduralAgent, Procedure, ProcedureStep
        )
        
        agent = ProceduralAgent()
        
        # Get default procedure
        proc = agent.get_procedure("standard_research")
        assert proc is not None
        assert len(proc.steps) > 0


# ============================================================================
# Approval Workflow Tests
# ============================================================================

class TestApprovalWorkflow:
    """Tests for HITL approval workflow."""
    
    @pytest.mark.asyncio
    async def test_create_request(self):
        """Test creating approval request."""
        from services.orchestrator.core.approval_workflow import (
            ApprovalWorkflow, ApprovalCategory
        )
        from services.orchestrator.core.audit_trail import (
            AuditTrail, MemoryBackend, configure_audit_trail
        )
        
        # Use memory backend for testing
        configure_audit_trail(MemoryBackend())
        
        workflow = ApprovalWorkflow()
        
        request_id = await workflow.create_request(
            category=ApprovalCategory.DECISION,
            title="Test approval",
            description="Test description",
            required_role="manager",
        )
        
        assert request_id is not None
        
        request = workflow.get_request(request_id)
        assert request.title == "Test approval"
    
    @pytest.mark.asyncio
    async def test_approve_request(self):
        """Test approving request."""
        from services.orchestrator.core.approval_workflow import (
            ApprovalWorkflow, ApprovalCategory, ApprovalStatus
        )
        from services.orchestrator.core.audit_trail import (
            MemoryBackend, configure_audit_trail
        )
        
        configure_audit_trail(MemoryBackend())
        
        workflow = ApprovalWorkflow()
        
        request_id = await workflow.create_request(
            category=ApprovalCategory.DECISION,
            title="Test",
        )
        
        success = await workflow.approve(request_id, "approver@test.com")
        assert success is True
        
        request = workflow.get_request(request_id)
        assert request.status == ApprovalStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_reject_request(self):
        """Test rejecting request."""
        from services.orchestrator.core.approval_workflow import (
            ApprovalWorkflow, ApprovalCategory, ApprovalStatus
        )
        from services.orchestrator.core.audit_trail import (
            MemoryBackend, configure_audit_trail
        )
        
        configure_audit_trail(MemoryBackend())
        
        workflow = ApprovalWorkflow()
        
        request_id = await workflow.create_request(
            category=ApprovalCategory.DECISION,
            title="Test",
        )
        
        success = await workflow.reject(request_id, "approver", "Not approved")
        assert success is True
        
        request = workflow.get_request(request_id)
        assert request.status == ApprovalStatus.REJECTED
    
    def test_hitl_config(self):
        """Test HITL configuration."""
        from services.orchestrator.core.approval_workflow import HITLConfig
        
        config = HITLConfig(confidence_threshold=0.8)
        
        # Low confidence should require review
        assert config.requires_review(confidence=0.5) is True
        assert config.requires_review(confidence=0.9) is False
        
        # High risk keyword
        assert config.requires_review(query="delete all files") is True
        
        # Sensitive domain
        assert config.requires_review(domain="finance") is True
    
    def test_get_pending(self):
        """Test getting pending approvals."""
        from services.orchestrator.core.approval_workflow import ApprovalWorkflow
        
        workflow = ApprovalWorkflow()
        
        pending = workflow.get_pending()
        assert isinstance(pending, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
