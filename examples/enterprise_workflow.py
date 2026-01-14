#!/usr/bin/env python3
"""
Enterprise Workflow Example.

Demonstrates the full v3.0 enterprise kernel in action:
- Organization hierarchy
- Work unit management
- Inter-agent messaging
- Supervisor oversight
"""

import asyncio
from dataclasses import dataclass


async def main():
    """
    Simulates a 100K-employee-equivalent workflow.
    
    Scenario: Research company financials across multiple departments.
    """
    print("=" * 60)
    print("KEA v3.0 ENTERPRISE KERNEL DEMO")
    print("=" * 60)
    
    # =========================================
    # Step 1: Create Organization Structure
    # =========================================
    from services.orchestrator.core.organization import (
        Organization, Domain, Role, RoleType
    )
    
    print("\n📊 STEP 1: Creating Organization")
    print("-" * 40)
    
    org = Organization()
    
    # Create departments
    research = org.create_department("Research Division", Domain.RESEARCH, max_teams=5)
    finance = org.create_department("Finance Division", Domain.FINANCE, max_teams=3)
    analytics = org.create_department("Analytics Division", Domain.ANALYTICS, max_teams=4)
    
    # Create teams
    market_team = research.add_team("Market Analysis", max_agents=10)
    competitor_team = research.add_team("Competitor Intel", max_agents=5)
    quant_team = finance.add_team("Quantitative Analysis", max_agents=8)
    data_team = analytics.add_team("Data Science", max_agents=6)
    
    # Define roles
    researcher_role = Role(
        name="Research Analyst",
        role_type=RoleType.RESEARCHER,
        system_prompt="You are a thorough research analyst...",
        allowed_tools=["web_search", "pdf_extract", "database"],
        can_spawn=True,
        can_escalate=True,
    )
    
    quant_role = Role(
        name="Quantitative Analyst",
        role_type=RoleType.ANALYST,
        system_prompt="You are a quantitative analyst...",
        allowed_tools=["pandas", "sql", "visualization"],
        can_spawn=False,
        can_escalate=True,
        max_concurrent=3,
    )
    
    reviewer_role = Role(
        name="Senior Reviewer",
        role_type=RoleType.REVIEWER,
        system_prompt="You review and validate research output...",
        allowed_tools=["fact_check", "validate"],
        can_spawn=False,
        can_escalate=True,
    )
    
    # Spawn agents
    for _ in range(5):
        market_team.add_agent(researcher_role)
    for _ in range(3):
        quant_team.add_agent(quant_role)
    data_team.add_agent(reviewer_role)
    
    print(f"✅ Created {len(org.list_departments())} departments")
    print(f"✅ Total agents: {org.total_agents}")
    print(f"   - Research: {research.total_agents}")
    print(f"   - Finance: {finance.total_agents}")
    print(f"   - Analytics: {analytics.total_agents}")
    
    # =========================================
    # Step 2: Create Work Units
    # =========================================
    from services.orchestrator.core.work_unit import (
        WorkBoard, WorkUnit, WorkType, Priority
    )
    
    print("\n📋 STEP 2: Creating Work Units")
    print("-" * 40)
    
    board = WorkBoard()
    
    # Primary research task
    main_research = WorkUnit.create(
        title="Comprehensive Tesla Analysis 2024",
        work_type=WorkType.RESEARCH,
        description="Full financial and competitive analysis of Tesla",
        priority=Priority.HIGH,
    )
    board.add(main_research)
    
    # Dependent tasks
    revenue_analysis = WorkUnit.create(
        title="Revenue Stream Breakdown",
        work_type=WorkType.ANALYSIS,
        priority=Priority.HIGH,
        dependencies=[main_research.work_id],
    )
    board.add(revenue_analysis)
    
    competitor_analysis = WorkUnit.create(
        title="Competitor Comparison: Ford, GM, Rivian",
        work_type=WorkType.ANALYSIS,
        priority=Priority.NORMAL,
    )
    board.add(competitor_analysis)
    
    data_validation = WorkUnit.create(
        title="Data Quality Review",
        work_type=WorkType.REVIEW,
        priority=Priority.NORMAL,
    )
    board.add(data_validation)
    
    print(f"✅ Created {board.stats['total']} work units")
    print(f"   - High priority: {board.stats['by_priority']['HIGH']}")
    print(f"   - Pending: {board.stats['by_status']['pending']}")
    
    # =========================================
    # Step 3: Setup Messaging
    # =========================================
    from services.orchestrator.core.messaging import (
        MessageBus, Message, MessageType
    )
    
    print("\n📨 STEP 3: Setting Up Message Bus")
    print("-" * 40)
    
    bus = MessageBus()
    
    # Track received messages
    messages_log = []
    
    # Define agent handlers
    async def market_handler(msg: Message):
        messages_log.append(f"[Market] Received: {msg.content.get('instruction', 'N/A')[:30]}")
        if msg.message_type == MessageType.REQUEST:
            response = msg.create_response({"status": "acknowledged", "eta": "2 hours"})
            await bus.send(response)
    
    async def quant_handler(msg: Message):
        messages_log.append(f"[Quant] Received: {msg.content.get('instruction', 'N/A')[:30]}")
    
    async def supervisor_handler(msg: Message):
        messages_log.append(f"[Supervisor] Alert: {msg.message_type.value}")
    
    # Subscribe agents
    await bus.subscribe("market_lead", market_handler)
    await bus.subscribe("quant_lead", quant_handler)
    await bus.subscribe("supervisor_1", supervisor_handler)
    
    print(f"✅ Registered {bus.stats['subscribers']} message handlers")
    
    # =========================================
    # Step 4: Execute Workflow
    # =========================================
    print("\n🚀 STEP 4: Executing Workflow")
    print("-" * 40)
    
    # Assign work
    board.assign(main_research.work_id, "market_lead", research.dept_id)
    board.assign(competitor_analysis.work_id, "quant_lead", finance.dept_id)
    
    print(f"✅ Assigned {main_research.title[:30]}... to market_lead")
    print(f"✅ Assigned {competitor_analysis.title[:30]}... to quant_lead")
    
    # Send coordination message
    await bus.send(Message.create(
        from_agent="orchestrator",
        to_agent="market_lead",
        message_type=MessageType.REQUEST,
        content={
            "instruction": "Begin Tesla comprehensive analysis",
            "deadline": "2024-12-01",
            "priority": "high",
        }
    ))
    
    # Broadcast status update
    await bus.broadcast(
        from_agent="orchestrator",
        content={"announcement": "Research sprint started"},
    )
    
    # Simulate work progress
    main_research.start()
    main_research.update_progress(0.3)
    print(f"✅ Work progress: {main_research.progress:.0%}")
    
    # =========================================
    # Step 5: Supervisor Oversight
    # =========================================
    from services.orchestrator.core.supervisor import (
        Supervisor, QualityCheck, CheckResult, EscalationType
    )
    
    print("\n👁️ STEP 5: Supervisor Oversight")
    print("-" * 40)
    
    supervisor = Supervisor()
    
    # Add quality checkers
    async def check_completeness(output):
        has_revenue = "revenue" in str(output).lower()
        return QualityCheck(
            "completeness", 
            CheckResult.PASS if has_revenue else CheckResult.FAIL,
            score=0.9 if has_revenue else 0.3
        )
    
    async def check_citations(output):
        has_sources = "source" in str(output).lower()
        return QualityCheck(
            "citations",
            CheckResult.PASS if has_sources else CheckResult.WARN,
            score=0.8 if has_sources else 0.5
        )
    
    supervisor.quality_gate.add_checker("completeness", check_completeness)
    supervisor.quality_gate.add_checker("citations", check_citations)
    
    # Simulate output review
    sample_output = {
        "title": "Tesla Revenue Analysis",
        "revenue": "$81.46 billion (2023)",
        "source": "Tesla 10-K Filing",
        "growth": "19% YoY"
    }
    
    review = await supervisor.review_output(main_research.work_id, sample_output)
    print(f"✅ Quality Review: {review.summary}")
    
    # Monitor team health
    @dataclass
    class TeamSnapshot:
        team_id: str
        utilization: float
        agents: list
    
    snapshot = TeamSnapshot(market_team.team_id, market_team.utilization, market_team.agents)
    health = await supervisor.monitor_team(snapshot)
    print(f"✅ Team Health: {'Healthy' if health.healthy else 'Issues Detected'}")
    
    # Complete work
    if review.passed:
        board.complete(main_research.work_id, result=sample_output)
        print(f"✅ Work completed: {main_research.title[:30]}...")
    else:
        # Escalate for revision
        await supervisor.escalate_to_human(
            EscalationType.QUALITY,
            source_agent="supervisor_1",
            context={"review": review.summary},
            message="Output did not meet quality threshold",
            work_id=main_research.work_id,
        )
        print(f"⚠️ Escalated: {main_research.work_id}")
    
    # =========================================
    # Summary
    # =========================================
    print("\n" + "=" * 60)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Organization: {len(org.list_departments())} departments, {org.total_agents} agents")
    print(f"Work Board: {board.stats['by_status']}")
    print(f"Messages Processed: {bus.stats['total_messages']}")
    print(f"Pending Escalations: {supervisor.pending_escalation_count}")
    print("\nMessage Log:")
    for log in messages_log[-5:]:
        print(f"  - {log}")
    print("\n✅ Enterprise workflow demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
