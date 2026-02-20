#!/usr/bin/env python
"""
Standalone v2.x Features Verification.

Run directly: python tests/verify/verify_v2_features.py

No pytest required - just run with Python.
Tests v2.x features: conversation, curiosity, degradation, recovery.
"""

import asyncio
import sys
sys.path.insert(0, '.')


def print_header(title):
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def print_ok(msg):
    print(f"✅ {msg}")


def print_fail(msg, error=None):
    print(f"❌ {msg}")
    if error:
        print(f"   Error: {error}")


def verify_conversation():
    """Verify conversation memory."""
    print_header("CONVERSATION MEMORY")
    
    try:
        from services.orchestrator.core.conversation import (
            ConversationManager, ConversationSession, Intent, IntentDetector
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Intent detection
        detector = IntentDetector()
        
        test_cases = [
            ("Research Tesla", Intent.NEW_TOPIC),
            ("What about their revenue?", Intent.FOLLOW_UP),
            ("Go deeper", Intent.DEEPER),
        ]
        
        for query, expected in test_cases:
            detected = detector.detect(query)
            print_ok(f"Intent: '{query[:20]}...' -> {detected.value}")
        
        # Session management
        manager = ConversationManager()
        session = manager.get_or_create_session("user_123")
        print_ok(f"Session created: {session.session_id}")
        
        # Add turns
        session.add_turn("user", "Research Tesla", Intent.NEW_TOPIC)
        session.add_turn("assistant", "Tesla is an EV company...")
        print_ok(f"Added {len(session.turns)} turns")
        
        return True
    except Exception as e:
        print_fail("Conversation test failed", e)
        return False


def verify_curiosity():
    """Verify curiosity engine."""
    print_header("CURIOSITY ENGINE")
    
    try:
        from services.orchestrator.core.curiosity import (
            CuriosityEngine, Fact, CuriosityQuestion, QuestionType
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        engine = CuriosityEngine()
        print_ok("CuriosityEngine created")
        
        # Create facts
        facts = [
            Fact(entity="Tesla", attribute="revenue", value="$81B", source="10-K"),
            Fact(entity="Tesla", attribute="growth", value="25%", source="10-K"),
            Fact(entity="Ford", attribute="revenue", value="$160B", source="10-K"),
            Fact(entity="Ford", attribute="growth", value="5%", source="10-K"),
        ]
        
        # Generate questions
        questions = engine.generate_questions(facts)
        
        print_ok(f"Generated {len(questions)} curiosity questions:")
        for q in questions[:3]:
            print(f"   • {q.text[:50]}...")
        
        return True
    except Exception as e:
        print_fail("Curiosity test failed", e)
        return False


def verify_degradation():
    """Verify graceful degradation."""
    print_header("GRACEFUL DEGRADATION")
    
    try:
        from services.orchestrator.core.degradation import (
            GracefulDegrader, DegradationLevel, get_degrader
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        degrader = GracefulDegrader(base_parallel=8, base_batch_size=1000)
        print_ok("GracefulDegrader created")
        
        # Test levels
        levels = ["NORMAL", "WARNING", "CRITICAL", "EMERGENCY"]
        
        for i, level_name in enumerate(levels):
            degrader.set_level(i)
            config = degrader.get_adjusted_config()
            print_ok(f"{level_name}: parallel={config['parallel']}, batch={config['batch_size']}")
        
        # Reset to normal
        degrader.set_level(0)
        
        return True
    except Exception as e:
        print_fail("Degradation test failed", e)
        return False


async def verify_recovery():
    """Verify error recovery."""
    print_header("ERROR RECOVERY")
    
    try:
        from services.orchestrator.core.recovery import (
            retry, CircuitBreaker, classify_error, ErrorType, CircuitOpenError
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Error classification
        test_errors = [
            (Exception("Rate limit 429"), "transient"),
            (Exception("Timeout"), "timeout"),
            (Exception("Auth failed 401"), "permanent"),
        ]
        
        for error, expected_type in test_errors:
            result = classify_error(error)
            print_ok(f"Classify '{str(error)[:20]}': {result.value}")
        
        # Circuit breaker
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for i in range(3):
            breaker.record_failure(Exception(f"Fail {i}"))
        
        assert breaker.state == "open"
        print_ok("Circuit breaker opens after 3 failures")
        
        # Test retry
        attempt_count = 0
        
        @retry(max_attempts=3, base_delay=0.01)
        async def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Transient error 429")
            return "success"
        
        result = await flaky_func()
        assert result == "success"
        print_ok(f"Retry succeeded after {attempt_count} attempts")
        
        return True
    except Exception as e:
        print_fail("Recovery test failed", e)
        return False


def verify_prompt_factory():
    """Verify prompt factory."""
    print_header("PROMPT FACTORY")
    
    try:
        from services.orchestrator.core.prompt_factory import (
            PromptFactory, PromptTemplate, get_prompt_factory
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        factory = PromptFactory()
        print_ok("PromptFactory created")
        
        # Create template
        template = PromptTemplate(
            name="researcher",
            base_prompt="You are a research assistant",
            variables=["topic", "depth"],
        )
        
        factory.register("researcher", template)
        print_ok("Template registered")
        
        # Build prompt
        prompt = factory.build("researcher", topic="Tesla", depth="detailed")
        print_ok(f"Prompt built: {len(prompt)} chars")
        
        return True
    except Exception as e:
        print_fail("Prompt factory test failed", e)
        return False


def verify_hardware():
    """Verify hardware detection."""
    print_header("HARDWARE DETECTION")
    
    try:
        from shared.hardware.detector import HardwareDetector
        from shared.hardware.monitor import HardwareMonitor
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        detector = HardwareDetector()
        info = detector.detect()
        
        print_ok(f"CPU: {info.cpu_count} cores")
        print_ok(f"Memory: {info.memory_gb:.1f} GB")
        print_ok(f"Platform: {info.platform}")
        
        return True
    except Exception as e:
        print_fail("Hardware test failed", e)
        return False


async def main():
    """Run all v2.x verification tests."""
    print("\n" + "=" * 60)
    print("🚀 PROJECT v2.x FEATURES VERIFICATION")
    print("=" * 60)
    print("\nRunning standalone Python verification (no pytest)...")
    
    results = {}
    
    # Synchronous tests
    results["Conversation"] = verify_conversation()
    results["Curiosity"] = verify_curiosity()
    results["Degradation"] = verify_degradation()
    results["Prompt Factory"] = verify_prompt_factory()
    results["Hardware"] = verify_hardware()
    
    # Async tests
    results["Recovery"] = await verify_recovery()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
