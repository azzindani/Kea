"""
Unit Tests: Orchestrator Core - Recovery and Curiosity.

Tests for recovery mechanisms and curiosity engine.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.orchestrator.core.recovery import (
    RecoveryManager,
    RecoveryStrategy,
)
from services.orchestrator.core.curiosity import (
    CuriosityEngine,
    CuriosityScore,
)


class TestRecoveryStrategy:
    """Test RecoveryStrategy enum."""
    
    def test_retry_strategy(self):
        """Test retry strategy."""
        assert RecoveryStrategy.RETRY.value == "retry"
    
    def test_fallback_strategy(self):
        """Test fallback strategy."""
        assert RecoveryStrategy.FALLBACK.value == "fallback"
    
    def test_skip_strategy(self):
        """Test skip strategy."""
        assert RecoveryStrategy.SKIP.value == "skip"


class TestRecoveryManager:
    """Test RecoveryManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager for testing."""
        return RecoveryManager()
    
    def test_manager_init(self, manager):
        """Test manager initialization."""
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_recover_with_retry(self, manager):
        """Test recovery with retry strategy."""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"
        
        result = await manager.with_recovery(
            failing_then_success,
            strategy=RecoveryStrategy.RETRY,
            max_attempts=3,
        )
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_recover_with_fallback(self, manager):
        """Test recovery with fallback."""
        async def failing_func():
            raise Exception("Always fails")
        
        async def fallback_func():
            return "fallback value"
        
        result = await manager.with_recovery(
            failing_func,
            strategy=RecoveryStrategy.FALLBACK,
            fallback=fallback_func,
        )
        
        assert result == "fallback value"
    
    @pytest.mark.asyncio
    async def test_recover_with_skip(self, manager):
        """Test recovery with skip strategy."""
        async def failing_func():
            raise Exception("Error")
        
        result = await manager.with_recovery(
            failing_func,
            strategy=RecoveryStrategy.SKIP,
        )
        
        assert result is None


class TestCuriosityScore:
    """Test CuriosityScore dataclass."""
    
    def test_create_score(self):
        """Test score creation."""
        score = CuriosityScore(
            novelty=0.8,
            uncertainty=0.6,
            relevance=0.9,
        )
        
        assert score.novelty == 0.8
        assert score.uncertainty == 0.6
    
    def test_overall_score(self):
        """Test overall score calculation."""
        score = CuriosityScore(
            novelty=0.8,
            uncertainty=0.6,
            relevance=1.0,
        )
        
        overall = score.overall()
        
        assert 0 <= overall <= 1


class TestCuriosityEngine:
    """Test CuriosityEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return CuriosityEngine()
    
    def test_engine_init(self, engine):
        """Test engine initialization."""
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_evaluate_query(self, engine):
        """Test evaluating query curiosity."""
        with patch.object(engine, "_calculate_novelty") as mock_novelty:
            mock_novelty.return_value = 0.7
            
            with patch.object(engine, "_calculate_uncertainty") as mock_uncertainty:
                mock_uncertainty.return_value = 0.5
                
                score = await engine.evaluate("What is quantum computing?")
                
                assert isinstance(score, CuriosityScore)
    
    @pytest.mark.asyncio
    async def test_should_explore(self, engine):
        """Test exploration decision."""
        with patch.object(engine, "evaluate") as mock:
            mock.return_value = CuriosityScore(
                novelty=0.9,
                uncertainty=0.8,
                relevance=0.9,
            )
            
            should = await engine.should_explore("Novel topic?")
            
            assert should is True
    
    @pytest.mark.asyncio
    async def test_should_not_explore_low_score(self, engine):
        """Test no exploration for low scores."""
        with patch.object(engine, "evaluate") as mock:
            mock.return_value = CuriosityScore(
                novelty=0.1,
                uncertainty=0.1,
                relevance=0.2,
            )
            
            should = await engine.should_explore("Boring topic")
            
            assert should is False
