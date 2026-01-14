#!/usr/bin/env python
"""
Standalone v3.0 Enterprise Kernel Verification.

Run directly: python tests/verify/verify_enterprise_kernel.py

No pytest required - just run with Python.
Tests the full v3.0 enterprise kernel components.
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


def print_skip(msg):
    print(f"⏭️  {msg}")


def verify_organization():
    """Verify organization module."""
    print_header("ORGANIZATION MODULE")
    
    try:
        from services.orchestrator.core.organization import (
            Organization, Department, Team, Role, RoleType, AgentInstance, Domain
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Create organization
        org = Organization()
        print_ok("Organization created")
        
        # Create departments
        research = org.create_department("Research", Domain.RESEARCH, max_teams=5)
        finance = org.create_department("Finance", Domain.FINANCE, max_teams=3)
        print_ok(f"Created 2 departments")
        
        # Create teams
        team = research.add_team("Market Analysis", max_agents=10)
        print_ok(f"Created team: {team.name}")
        
        # Create roles and agents
        analyst_role = Role(
            name="Analyst",
            role_type=RoleType.ANALYST,
            system_prompt="You analyze data",
            allowed_tools=["pandas", "sql"],
        )
        
        agent = team.add_agent(analyst_role)
        print_ok(f"Created agent: {agent.agent_id}")
        
        # Verify stats
        stats = org.stats
        assert stats["departments"] == 2
        assert stats["total_agents"] == 1
        print_ok(f"Organization stats: {stats}")
        
        return True
    except Exception as e:
        print_fail("Organization test failed", e)
        return False


def verify_work_unit():
    """Verify work unit module."""
    print_header("WORK UNIT MODULE")
    
    try:
        from services.orchestrator.core.work_unit import (
            WorkUnit, WorkBoard, WorkType, WorkStatus, Priority
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Create work board
        board = WorkBoard()
        print_ok("WorkBoard created")
        
        # Create work units
        work1 = WorkUnit.create(
            title="Research Tesla Financials",
            work_type=WorkType.RESEARCH,
            priority=Priority.HIGH,
        )
        board.add(work1)
        print_ok(f"Created work: {work1.work_id}")
        
        work2 = WorkUnit.create(
            title="Analyze Data",
            work_type=WorkType.ANALYSIS,
            priority=Priority.NORMAL,
            dependencies=[work1.work_id],
        )
        board.add(work2)
        print_ok(f"Created dependent work: {work2.work_id}")
        
        # Test lifecycle
        work1.start()
        assert work1.status == WorkStatus.IN_PROGRESS
        print_ok("Work started")
        
        work1.update_progress(0.5)
        print_ok(f"Progress updated: {work1.progress:.0%}")
        
        board.complete(work1.work_id, result={"revenue": "$81B"})
        assert work1.status == WorkStatus.COMPLETED
        print_ok("Work completed")
        
        # Verify stats
        stats = board.stats
        print_ok(f"Board stats: {stats}")
        
        return True
    except Exception as e:
        print_fail("Work unit test failed", e)
        return False


async def verify_messaging():
    """Verify messaging module."""
    print_header("MESSAGING MODULE")
    
    try:
        from services.orchestrator.core.messaging import (
            Message, MessageBus, MessageType
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Create message bus
        bus = MessageBus()
        print_ok("MessageBus created")
        
        # Track received messages
        received = []
        
        async def handler(msg):
            received.append(msg)
        
        # Subscribe
        await bus.subscribe("agent_1", handler)
        await bus.subscribe("agent_2", lambda m: None)
        print_ok(f"Subscribed {bus.stats['subscribers']} handlers")
        
        # Send message
        msg = Message.create(
            from_agent="agent_2",
            to_agent="agent_1",
            message_type=MessageType.INFO,
            content={"hello": "world"}
        )
        await bus.send(msg)
        print_ok("Message sent")
        
        assert len(received) == 1
        print_ok(f"Message received: {received[0].content}")
        
        # Broadcast
        await bus.broadcast("agent_2", {"announcement": "Hello all!"})
        print_ok(f"Broadcast sent, total messages: {bus.stats['total_messages']}")
        
        return True
    except Exception as e:
        print_fail("Messaging test failed", e)
        return False


async def verify_supervisor():
    """Verify supervisor module."""
    print_header("SUPERVISOR MODULE")
    
    try:
        from services.orchestrator.core.supervisor import (
            Supervisor, QualityCheck, CheckResult, EscalationType
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Create supervisor
        supervisor = Supervisor()
        print_ok("Supervisor created")
        
        # Add quality checker
        async def check_quality(output):
            has_data = isinstance(output, dict) and len(output) > 0
            return QualityCheck(
                name="data_check",
                result=CheckResult.PASS if has_data else CheckResult.FAIL,
                score=0.9 if has_data else 0.3,
            )
        
        supervisor.quality_gate.add_checker("quality", check_quality)
        print_ok("Quality checker added")
        
        # Test review
        good_output = {"revenue": "$81B", "growth": "25%"}
        review = await supervisor.review_output("work_123", good_output)
        
        assert review.passed is True
        print_ok(f"Review passed: {review.summary}")
        
        # Test escalation
        esc_id = await supervisor.escalate_to_human(
            EscalationType.DECISION,
            source_agent="agent_1",
            context={"question": "Need approval"},
            message="Human input required",
        )
        print_ok(f"Escalation created: {esc_id}")
        
        assert supervisor.pending_escalation_count == 1
        print_ok(f"Pending escalations: {supervisor.pending_escalation_count}")
        
        return True
    except Exception as e:
        print_fail("Supervisor test failed", e)
        return False


def verify_guards():
    """Verify guards module."""
    print_header("GUARDS MODULE")
    
    try:
        from services.orchestrator.core.guards import (
            ResourceGuard, RateLimiter, get_resource_guard
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        # Test rate limiter
        limiter = RateLimiter(max_per_minute=5)
        
        allowed = 0
        for i in range(10):
            if limiter.check("test_key"):
                allowed += 1
        
        assert allowed == 5
        print_ok(f"RateLimiter: {allowed}/10 allowed")
        
        # Test resource guard
        guard = ResourceGuard(max_agents_per_minute=10)
        print_ok("ResourceGuard created")
        
        guard.register_agent_spawn()
        guard.register_agent_spawn()
        print_ok(f"Active agents: {guard.active_agent_count}")
        
        return True
    except Exception as e:
        print_fail("Guards test failed", e)
        return False


async def verify_kill_switch():
    """Verify kill switch module."""
    print_header("KILL SWITCH MODULE")
    
    try:
        from services.orchestrator.core.kill_switch import (
            KillSwitch, get_kill_switch
        )
        print_ok("Imports successful")
    except ImportError as e:
        print_fail("Import failed", e)
        return False
    
    try:
        switch = KillSwitch()
        
        # Normal operation
        assert switch.can_proceed() is True
        print_ok("Normal operation allowed")
        
        # Blacklist tool
        switch.blacklist_tool("bad_tool", reason="Testing")
        assert switch.can_proceed(tool_name="bad_tool") is False
        assert switch.can_proceed(tool_name="good_tool") is True
        print_ok("Tool blacklisting works")
        
        switch.unblacklist_tool("bad_tool")
        
        # Emergency stop
        await switch.emergency_stop("Test emergency")
        assert switch.is_emergency_stopped is True
        assert switch.can_proceed() is False
        print_ok("Emergency stop works")
        
        await switch.resume()
        assert switch.can_proceed() is True
        print_ok("Resume works")
        
        return True
    except Exception as e:
        print_fail("Kill switch test failed", e)
        return False


async def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("🚀 KEA v3.0 ENTERPRISE KERNEL VERIFICATION")
    print("=" * 60)
    print("\nRunning standalone Python verification (no pytest)...")
    
    results = {}
    
    # Synchronous tests
    results["Organization"] = verify_organization()
    results["Work Unit"] = verify_work_unit()
    results["Guards"] = verify_guards()
    
    # Async tests
    results["Messaging"] = await verify_messaging()
    results["Supervisor"] = await verify_supervisor()
    results["Kill Switch"] = await verify_kill_switch()
    
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
