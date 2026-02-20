"""
Tests for Conversational Memory Manager.
"""

import pytest


class TestIntent:
    """Tests for intent classification."""
    
    def test_intent_values(self):
        """Test intent enum values."""
        from services.orchestrator.core.conversation import Intent
        
        assert Intent.FOLLOW_UP.value == "follow_up"
        assert Intent.DEEPER.value == "deeper"
        assert Intent.REVISE.value == "revise"
        assert Intent.NEW_TOPIC.value == "new_topic"
        assert Intent.COMPARE.value == "compare"
        assert Intent.CLARIFY.value == "clarify"
        assert Intent.CONFIRM.value == "confirm"
        
        print("\n✅ Intent enum values correct")


class TestIntentDetector:
    """Tests for intent detection."""
    
    def test_detect_follow_up(self):
        """Test follow-up intent detection."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # Follow-up patterns
        assert detector.detect("What about Ford?") == Intent.FOLLOW_UP
        assert detector.detect("And the Philippines?") == Intent.FOLLOW_UP
        assert detector.detect("Also check Microsoft") == Intent.FOLLOW_UP
        
        print("\n✅ Follow-up detection works")
    
    def test_detect_deeper(self):
        """Test deeper intent detection."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        assert detector.detect("Go deeper on this") == Intent.DEEPER
        assert detector.detect("More details please") == Intent.DEEPER
        assert detector.detect("Expand on the revenue section") == Intent.DEEPER
        
        print("\n✅ Deeper detection works")
    
    def test_detect_revise_with_pattern(self):
        """Test revise intent detection with actual patterns."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # Use actual patterns from the detector
        assert detector.detect("Recalculate with new data") == Intent.REVISE
        assert detector.detect("Redo the analysis") == Intent.REVISE
        
        print("\n✅ Revise detection works")
    
    def test_detect_new_topic_without_session(self):
        """Test new topic detection without existing session."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # Without session context, new queries default to NEW_TOPIC
        result = detector.detect("Research Tesla stock performance", None)
        assert result == Intent.NEW_TOPIC
        
        print("\n✅ New topic detection works")
    
    def test_detect_compare_with_pattern(self):
        """Test compare intent detection."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # Use actual patterns
        assert detector.detect("Compare with last week's data") == Intent.COMPARE
        
        print("\n✅ Compare detection works")
    
    def test_detect_clarify(self):
        """Test clarify intent detection."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # Use actual patterns
        assert detector.detect("What do you mean by that?") == Intent.CLARIFY
        assert detector.detect("Can you explain that?") == Intent.CLARIFY
        
        print("\n✅ Clarify detection works")


class TestConversationSession:
    """Tests for conversation session."""
    
    def test_create_session(self):
        """Test session creation."""
        from services.orchestrator.core.conversation import ConversationSession
        
        session = ConversationSession(session_id="test-123")
        
        assert session.session_id == "test-123"
        assert len(session.turns) == 0
        
        print("\n✅ Session created")
    
    def test_add_turn(self):
        """Test adding turns to session."""
        from services.orchestrator.core.conversation import ConversationSession, Intent
        
        session = ConversationSession(session_id="test-123")
        
        session.add_turn("user", "Research Tesla", Intent.NEW_TOPIC)
        session.add_turn("assistant", "Here is the Tesla research...")
        
        assert len(session.turns) == 2
        assert session.turns[0].role == "user"
        assert session.turns[0].intent == Intent.NEW_TOPIC
        assert session.turns[1].role == "assistant"
        
        print("\n✅ Turns added correctly")
    
    def test_get_summary(self):
        """Test session summary."""
        from services.orchestrator.core.conversation import ConversationSession
        
        session = ConversationSession(session_id="test-123", topic="Tesla Research")
        session.add_turn("user", "Research Tesla")
        session.add_turn("assistant", "Tesla is an EV company...")
        
        summary = session.get_summary()
        
        # Summary uses "User" and "Project" prefixes
        assert "User" in summary
        assert "Project" in summary
        
        print("\n✅ Summary generation works")


class TestSmartContextBuilder:
    """Tests for smart context injection."""
    
    def test_build_context(self):
        """Test context building."""
        from services.orchestrator.core.conversation import (
            SmartContextBuilder, ConversationSession
        )
        
        session = ConversationSession(session_id="test", topic="Tesla Analysis")
        session.facts = ["Tesla revenue: $81B", "Tesla growth: 25%"]
        session.add_turn("user", "What about Tesla?")
        
        builder = SmartContextBuilder(max_facts=3)
        context = builder.build_context("Follow up on revenue", session)
        
        assert "revenue" in context.lower() or "Tesla" in context
        
        print("\n✅ Context building works")
    
    def test_filter_relevant_facts(self):
        """Test fact filtering."""
        from services.orchestrator.core.conversation import SmartContextBuilder
        
        builder = SmartContextBuilder()
        
        facts = [
            "Tesla revenue: $81B",
            "Ford revenue: $160B",
            "Apple market cap: $3T",
        ]
        
        filtered = builder._filter_relevant("Tesla financial", facts)
        
        # Should prioritize Tesla-related facts
        assert len(filtered) <= builder.max_facts
        
        print("\n✅ Fact filtering works")


class TestConversationManager:
    """Tests for conversation manager."""
    
    def test_get_or_create_session(self):
        """Test session retrieval/creation."""
        from services.orchestrator.core.conversation import ConversationManager
        
        manager = ConversationManager()
        
        session1 = manager.get_or_create_session("session-1")
        session2 = manager.get_or_create_session("session-1")
        session3 = manager.get_or_create_session("session-2")
        
        assert session1 is session2  # Same session
        assert session1 is not session3  # Different session
        
        print("\n✅ Session management works")
    
    def test_requires_confirmation(self):
        """Test confirmation requirement check."""
        from services.orchestrator.core.conversation import IntentDetector, Intent
        
        detector = IntentDetector()
        
        # DEEPER and REVISE require confirmation
        assert detector.requires_confirmation(Intent.DEEPER) is True
        assert detector.requires_confirmation(Intent.REVISE) is True
        
        # Others don't
        assert detector.requires_confirmation(Intent.FOLLOW_UP) is False
        assert detector.requires_confirmation(Intent.NEW_TOPIC) is False
        
        print("\n✅ Confirmation check works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
