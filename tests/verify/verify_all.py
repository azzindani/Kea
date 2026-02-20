#!/usr/bin/env python
"""
Standalone Full System Health Check.

Run directly: python tests/verify/verify_all.py

No pytest required - comprehensive system health check.
"""

import asyncio
import sys
import time
sys.path.insert(0, '.')


def print_banner(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print('─' * 50)


def check(name, condition, details=""):
    if condition:
        print(f"  ✅ {name}" + (f" ({details})" if details else ""))
        return True
    else:
        print(f"  ❌ {name}" + (f" - {details}" if details else ""))
        return False


async def verify_core_imports():
    """Verify all core imports work."""
    print_section("CORE IMPORTS")
    
    results = []
    
    modules = [
        ("services.orchestrator.core.organization", ["Organization", "Department", "Team"]),
        ("services.orchestrator.core.work_unit", ["WorkUnit", "WorkBoard", "Priority"]),
        ("services.orchestrator.core.messaging", ["Message", "MessageBus"]),
        ("services.orchestrator.core.supervisor", ["Supervisor", "QualityCheck"]),
        ("services.orchestrator.core.guards", ["ResourceGuard", "RateLimiter"]),
        ("services.orchestrator.core.kill_switch", ["KillSwitch"]),
        ("services.orchestrator.core.conversation", ["ConversationManager"]),
        ("services.orchestrator.core.curiosity", ["CuriosityEngine"]),
        ("services.orchestrator.core.degradation", ["GracefulDegrader"]),
        ("services.orchestrator.core.recovery", ["retry", "CircuitBreaker"]),
        ("services.orchestrator.core.prompt_factory", ["PromptFactory"]),
        ("services.orchestrator.core.graph", ["ResearchGraph"]),
        ("services.orchestrator.nodes.planner", ["plan"]),
        ("services.orchestrator.agents.generator", ["Generator"]),
    ]
    
    for module_path, classes in modules:
        try:
            module = __import__(module_path, fromlist=classes)
            for cls in classes:
                getattr(module, cls)
            results.append(check(module_path.split(".")[-1], True))
        except Exception as e:
            results.append(check(module_path.split(".")[-1], False, str(e)[:50]))
    
    return all(results)


async def verify_mcp_servers():
    """Verify MCP server imports."""
    print_section("MCP SERVERS")
    
    results = []
    
    servers = [
        "analysis_server",
        "python_server",
        "scraper_server",
        "search_server",
        "vision_server",
        "academic_server",
        "analytics_server",
        "crawler_server",
        "data_sources_server",
        "document_server",
        "ml_server",
        "qualitative_server",
        "regulatory_server",
        "security_server",
        "tool_discovery_server",
        "visualization_server",
    ]
    
    for server in servers:
        try:
            module = __import__(f"mcp_servers.{server}.server", fromlist=["server"])
            results.append(check(server, True))
        except Exception as e:
            results.append(check(server, False, str(e)[:40]))
    
    return all(results)


async def verify_shared_modules():
    """Verify shared module imports."""
    print_section("SHARED MODULES")
    
    results = []
    
    modules = [
        ("shared.hardware.detector", "HardwareDetector"),
        ("shared.storage.hf_sync", "HuggingFaceSync"),
        ("shared.mcp.client", "MCPClient"),
        ("shared.mcp.protocol", "MCPProtocol"),
        ("shared.tools.jit_loader", "JITLoader"),
        ("shared.config", "settings"),
    ]
    
    for module_path, item in modules:
        try:
            module = __import__(module_path, fromlist=[item])
            getattr(module, item)
            results.append(check(module_path.split(".")[-1], True))
        except Exception as e:
            results.append(check(module_path.split(".")[-1], False, str(e)[:40]))
    
    return all(results)


async def verify_functional_tests():
    """Run quick functional tests."""
    print_section("FUNCTIONAL TESTS")
    
    results = []
    
    # 1. Organization hierarchy
    try:
        from services.orchestrator.core.organization import Organization, Domain, Role, RoleType
        org = Organization()
        dept = org.create_department("Test", Domain.RESEARCH)
        team = dept.add_team("TestTeam", max_agents=3)
        role = Role("Tester", RoleType.ANALYST, "Test")
        agent = team.add_agent(role)
        results.append(check("Organization hierarchy", org.total_agents == 1, "1 agent"))
    except Exception as e:
        results.append(check("Organization hierarchy", False, str(e)[:40]))
    
    # 2. Work board
    try:
        from services.orchestrator.core.work_unit import WorkBoard, WorkUnit, WorkType
        board = WorkBoard()
        work = WorkUnit.create("Test", WorkType.RESEARCH)
        board.add(work)
        work.start()
        board.complete(work.work_id, result={"test": True})
        results.append(check("Work board lifecycle", work.result is not None))
    except Exception as e:
        results.append(check("Work board lifecycle", False, str(e)[:40]))
    
    # 3. Message bus
    try:
        from services.orchestrator.core.messaging import MessageBus, Message, MessageType
        bus = MessageBus()
        received = []
        await bus.subscribe("agent", lambda m: received.append(m))
        await bus.send(Message.create("other", "agent", MessageType.INFO, {"test": 1}))
        results.append(check("Message bus", len(received) == 1, "1 message"))
    except Exception as e:
        results.append(check("Message bus", False, str(e)[:40]))
    
    # 4. Quality gate
    try:
        from services.orchestrator.core.supervisor import Supervisor, QualityCheck, CheckResult
        sup = Supervisor()
        async def checker(o): return QualityCheck("test", CheckResult.PASS, 0.9)
        sup.quality_gate.add_checker("t", checker)
        review = await sup.review_output("w1", {"data": 1})
        results.append(check("Quality gate", review.passed, "passed"))
    except Exception as e:
        results.append(check("Quality gate", False, str(e)[:40]))
    
    # 5. Rate limiter
    try:
        from services.orchestrator.core.guards import RateLimiter
        limiter = RateLimiter(max_per_minute=5)
        allowed = sum(1 for _ in range(10) if limiter.check("k"))
        results.append(check("Rate limiter", allowed == 5, f"{allowed}/10 allowed"))
    except Exception as e:
        results.append(check("Rate limiter", False, str(e)[:40]))
    
    # 6. Circuit breaker
    try:
        from services.orchestrator.core.recovery import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure(Exception("1"))
        cb.record_failure(Exception("2"))
        results.append(check("Circuit breaker", cb.state == "open", "opens correctly"))
    except Exception as e:
        results.append(check("Circuit breaker", False, str(e)[:40]))
    
    # 7. Kill switch
    try:
        from services.orchestrator.core.kill_switch import KillSwitch
        ks = KillSwitch()
        ks.blacklist_tool("bad")
        blocked = not ks.can_proceed(tool_name="bad")
        allowed = ks.can_proceed(tool_name="good")
        ks.unblacklist_tool("bad")
        results.append(check("Kill switch", blocked and allowed, "blacklist works"))
    except Exception as e:
        results.append(check("Kill switch", False, str(e)[:40]))
    
    return all(results)


async def main():
    """Run comprehensive system health check."""
    start_time = time.time()
    
    print_banner("🦜 PROJECT SYSTEM HEALTH CHECK")
    print(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    
    results = {}
    
    results["Core Imports"] = await verify_core_imports()
    results["MCP Servers"] = await verify_mcp_servers()
    results["Shared Modules"] = await verify_shared_modules()
    results["Functional Tests"] = await verify_functional_tests()
    
    # Summary
    duration = time.time() - start_time
    
    print_banner("📊 HEALTH CHECK SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "✅ HEALTHY" if success else "❌ ISSUES"
        print(f"  {name}: {status}")
    
    print(f"\n  Duration: {duration:.2f}s")
    print(f"  Result: {passed}/{total} categories healthy")
    
    if passed == total:
        print("\n  🎉 ALL SYSTEMS OPERATIONAL!")
    else:
        print("\n  ⚠️  Some systems have issues - check above for details")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
