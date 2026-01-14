"""
Tests for System Prompt Factory.
"""

import pytest


class TestDomainDetection:
    """Tests for domain detection."""
    
    def test_detect_finance_domain(self):
        """Test finance domain detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, Domain
        
        factory = PromptFactory()
        
        assert factory.detect_domain("What is Tesla's stock price?") == Domain.FINANCE
        assert factory.detect_domain("Analyze revenue growth") == Domain.FINANCE
        assert factory.detect_domain("P/E ratio comparison") == Domain.FINANCE
        assert factory.detect_domain("SEC 10-K filing analysis") == Domain.FINANCE
        
        print("\n✅ Finance domain detection works")
    
    def test_detect_medical_domain(self):
        """Test medical domain detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, Domain
        
        factory = PromptFactory()
        
        assert factory.detect_domain("Diabetes treatment options") == Domain.MEDICAL
        assert factory.detect_domain("Clinical trial results") == Domain.MEDICAL
        assert factory.detect_domain("Drug side effects") == Domain.MEDICAL
        
        print("\n✅ Medical domain detection works")
    
    def test_detect_legal_domain(self):
        """Test legal domain detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, Domain
        
        factory = PromptFactory()
        
        assert factory.detect_domain("Patent law requirements") == Domain.LEGAL
        assert factory.detect_domain("Contract compliance") == Domain.LEGAL
        assert factory.detect_domain("Court case analysis") == Domain.LEGAL
        
        print("\n✅ Legal domain detection works")
    
    def test_detect_engineering_domain(self):
        """Test engineering domain detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, Domain
        
        factory = PromptFactory()
        
        assert factory.detect_domain("API architecture design") == Domain.ENGINEERING
        assert factory.detect_domain("Database optimization") == Domain.ENGINEERING
        assert factory.detect_domain("Software scalability") == Domain.ENGINEERING
        
        print("\n✅ Engineering domain detection works")


class TestTaskTypeDetection:
    """Tests for task type detection."""
    
    def test_detect_compare_task(self):
        """Test compare task detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, TaskType
        
        factory = PromptFactory()
        
        assert factory.detect_task_type("Compare Tesla vs Ford") == TaskType.COMPARE
        assert factory.detect_task_type("What's the difference") == TaskType.COMPARE
        
        print("\n✅ Compare task detection works")
    
    def test_detect_summarize_task(self):
        """Test summarize task detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, TaskType
        
        factory = PromptFactory()
        
        assert factory.detect_task_type("Summarize this report") == TaskType.SUMMARIZE
        assert factory.detect_task_type("Give me a brief overview") == TaskType.SUMMARIZE
        
        print("\n✅ Summarize task detection works")
    
    def test_detect_explain_task(self):
        """Test explain task detection."""
        from services.orchestrator.core.prompt_factory import PromptFactory, TaskType
        
        factory = PromptFactory()
        
        assert factory.detect_task_type("Explain how this works") == TaskType.EXPLAIN
        assert factory.detect_task_type("Why did this happen") == TaskType.EXPLAIN
        
        print("\n✅ Explain task detection works")


class TestPromptGeneration:
    """Tests for prompt generation."""
    
    def test_generate_finance_prompt(self):
        """Test generating finance prompt."""
        from services.orchestrator.core.prompt_factory import generate_prompt, Domain
        
        result = generate_prompt("What is Apple's market cap?")
        
        assert result.domain == Domain.FINANCE
        assert "financial" in result.prompt.lower()
        assert len(result.prompt) > 100  # Should have substantial content
        
        print(f"\n✅ Generated finance prompt ({len(result.prompt)} chars)")
    
    def test_generate_with_context(self):
        """Test generating prompt with session context."""
        from services.orchestrator.core.prompt_factory import (
            PromptFactory, PromptContext, Domain, TaskType
        )
        
        factory = PromptFactory()
        
        context = PromptContext(
            query="Follow up on previous analysis",
            domain=Domain.FINANCE,
            task_type=TaskType.ANALYSIS,
            depth=3,
            audience="executive",
            session_summary="Previous research on tech stocks",
            previous_findings=["Apple revenue up 10%", "Microsoft cloud growth strong"],
        )
        
        result = factory.generate(context)
        
        assert "Session Context" in result.prompt
        assert "Previous Findings" in result.prompt
        assert "Executive" in result.prompt
        assert "DEEP" in result.prompt
        
        print("\n✅ Context-aware prompt generation works")
    
    def test_prompt_versioning(self):
        """Test prompt versioning."""
        from services.orchestrator.core.prompt_factory import generate_prompt
        
        result = generate_prompt("Test query")
        
        assert result.version is not None
        assert result.hash is not None
        assert len(result.hash) == 8
        
        print(f"\n✅ Prompt version: {result.version}, hash: {result.hash}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
