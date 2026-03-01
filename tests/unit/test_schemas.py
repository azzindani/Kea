"""
Unit Tests: Pydantic Schemas.

Tests for all Pydantic models in shared/schemas.py.
"""


import pytest


class TestAtomicFact:
    """Tests for AtomicFact schema."""

    def test_create_minimal(self):
        """Create fact with minimal fields."""
        from shared.schemas import AtomicFact

        fact = AtomicFact(
            fact_id="fact-123",
            entity="test entity",
            attribute="test attr",
            value="test value",
            source_url="https://example.com",
        )

        assert fact.fact_id == "fact-123"
        assert fact.entity == "test entity"
        assert fact.confidence_score == 0.8  # actual default from schema

    def test_create_full(self):
        """Create fact with all fields."""
        from shared.schemas import AtomicFact

        fact = AtomicFact(
            fact_id="fact-456",
            entity="Indonesia nickel",
            attribute="production",
            value="1.5 million tons",
            unit="tons",
            period="2024",
            source_url="https://example.com/report",
            source_title="Annual Report",
            confidence_score=0.95,
        )

        assert fact.unit == "tons"
        assert fact.period == "2024"
        assert fact.confidence_score == 0.95

    def test_confidence_bounds(self):
        """Confidence score accepts floats (no validation in schema)."""
        from shared.schemas import AtomicFact

        # Valid bounds
        fact_low = AtomicFact(
            fact_id="f1", entity="e", attribute="a", value="v",
            source_url="url", confidence_score=0.0
        )
        assert fact_low.confidence_score == 0.0

        fact_high = AtomicFact(
            fact_id="f2", entity="e", attribute="a", value="v",
            source_url="url", confidence_score=1.0
        )
        assert fact_high.confidence_score == 1.0

        # Schema doesn't enforce bounds, values are accepted
        fact_over = AtomicFact(
            fact_id="f3", entity="e", attribute="a", value="v",
            source_url="url", confidence_score=1.5
        )
        assert fact_over.confidence_score == 1.5


class TestSource:
    """Tests for Source schema."""

    def test_create_source(self):
        """Create source with all fields."""
        from shared.schemas import Source

        source = Source(
            url="https://example.com/article",
            title="Test Article",
            domain="example.com",
        )

        assert source.url == "https://example.com/article"
        assert source.domain == "example.com"


class TestJobRequest:
    """Tests for JobRequest schema."""

    def test_create_job_request(self):
        """Create job request."""
        from shared.schemas import JobRequest, JobType

        req = JobRequest(
            query="Test query",
            job_type=JobType.DEEP_RESEARCH,
        )

        assert req.query == "Test query"
        assert req.depth == 2  # actual default from schema
        assert req.max_sources == 10  # default

    def test_job_types(self):
        """All job types are valid."""
        from shared.schemas import JobRequest, JobType

        for job_type in JobType:
            req = JobRequest(query="test", job_type=job_type)
            assert req.job_type == job_type


class TestResearchState:
    """Tests for ResearchState schema."""

    def test_create_research_state(self):
        """Create research state."""
        from shared.schemas import ResearchState, ResearchStatus

        state = ResearchState(
            job_id="job-123",
            query="Test query",
        )

        assert state.job_id == "job-123"
        assert state.status == ResearchStatus.PENDING
        assert state.facts == []
        assert state.sources == []

    def test_research_status_progression(self):
        """Status can progress through states."""
        from shared.schemas import ResearchState, ResearchStatus

        state = ResearchState(job_id="j1", query="q")

        state.status = ResearchStatus.RUNNING
        assert state.status == ResearchStatus.RUNNING

        state.status = ResearchStatus.COMPLETED
        assert state.status == ResearchStatus.COMPLETED


class TestToolInvocation:
    """Tests for ToolInvocation schema."""

    def test_create_invocation(self):
        """Create tool invocation record."""
        from shared.schemas import ToolInvocation

        inv = ToolInvocation(
            tool_name="fetch_url",
            server_name="scraper_server",  # required field
            arguments={"url": "https://example.com"},
        )

        assert inv.tool_name == "fetch_url"
        assert inv.server_name == "scraper_server"
        assert inv.is_error == False
        assert inv.result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

