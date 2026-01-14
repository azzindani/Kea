"""
Tests for Organizational Hierarchy.
"""

import pytest


class TestRole:
    """Tests for Role model."""
    
    def test_create_role(self):
        """Test role creation."""
        from services.orchestrator.core.organization import Role, RoleType
        
        role = Role(
            name="Data Analyst",
            role_type=RoleType.ANALYST,
            system_prompt="You analyze data...",
            allowed_tools=["pandas", "sql"],
            can_spawn=False,
            can_escalate=True,
        )
        
        assert role.name == "Data Analyst"
        assert role.role_type == RoleType.ANALYST
        assert "pandas" in role.allowed_tools
        assert role.can_spawn is False
        
        print("\n✅ Role created correctly")
    
    def test_role_to_dict(self):
        """Test role serialization."""
        from services.orchestrator.core.organization import Role, RoleType
        
        role = Role("Researcher", RoleType.RESEARCHER, "Research things")
        data = role.to_dict()
        
        assert data["name"] == "Researcher"
        assert data["role_type"] == "researcher"
        
        print("\n✅ Role serialization works")


class TestAgentInstance:
    """Tests for AgentInstance."""
    
    def test_create_agent(self):
        """Test agent creation."""
        from services.orchestrator.core.organization import (
            AgentInstance, Role, RoleType
        )
        
        role = Role("Analyst", RoleType.ANALYST, "Analyze data")
        agent = AgentInstance.create(role, "team_123")
        
        assert agent.agent_id.startswith("agent_")
        assert agent.role == role
        assert agent.team_id == "team_123"
        assert agent.status == "idle"
        
        print(f"\n✅ Created agent: {agent.agent_id}")


class TestTeam:
    """Tests for Team."""
    
    def test_create_team(self):
        """Test team creation."""
        from services.orchestrator.core.organization import Team
        
        team = Team.create("Market Analysis", "dept_123", max_agents=5)
        
        assert team.name == "Market Analysis"
        assert team.team_id.startswith("team_")
        assert team.max_agents == 5
        assert len(team.agents) == 0
        
        print(f"\n✅ Created team: {team.team_id}")
    
    def test_add_agent_to_team(self):
        """Test adding agents to team."""
        from services.orchestrator.core.organization import Team, Role, RoleType
        
        team = Team.create("Analysis Team", "dept_1", max_agents=3)
        role = Role("Analyst", RoleType.ANALYST, "Analyze")
        
        # Add agents
        agent1 = team.add_agent(role)
        agent2 = team.add_agent(role)
        agent3 = team.add_agent(role)
        
        assert len(team.agents) == 3
        assert agent1 is not None
        
        # Should fail at capacity
        agent4 = team.add_agent(role)
        assert agent4 is None
        
        print("\n✅ Team capacity enforced")
    
    def test_team_utilization(self):
        """Test utilization calculation."""
        from services.orchestrator.core.organization import Team, Role, RoleType
        
        team = Team.create("Test Team", "dept_1", max_agents=4)
        role = Role("Worker", RoleType.EXECUTOR, "Execute")
        
        # Add 4 agents
        for _ in range(4):
            team.add_agent(role)
        
        # All idle
        assert team.utilization == 0.0
        
        # Set 2 as working
        team.agents[0].status = "working"
        team.agents[1].status = "working"
        
        assert team.utilization == 0.5  # 2/4
        
        print("\n✅ Utilization calculated correctly")


class TestDepartment:
    """Tests for Department."""
    
    def test_create_department(self):
        """Test department creation."""
        from services.orchestrator.core.organization import Department, Domain
        
        dept = Department.create("Research Dept", Domain.RESEARCH, max_teams=5)
        
        assert dept.name == "Research Dept"
        assert dept.domain == Domain.RESEARCH
        assert dept.dept_id.startswith("dept_")
        
        print(f"\n✅ Created department: {dept.dept_id}")
    
    def test_add_team_to_department(self):
        """Test adding teams to department."""
        from services.orchestrator.core.organization import Department, Domain
        
        dept = Department.create("Finance", Domain.FINANCE, max_teams=2)
        
        team1 = dept.add_team("Analysis", max_agents=5)
        team2 = dept.add_team("Reporting", max_agents=3)
        team3 = dept.add_team("Overflow", max_agents=2)  # Should fail
        
        assert len(dept.teams) == 2
        assert team1 is not None
        assert team2 is not None
        assert team3 is None  # At capacity
        
        print("\n✅ Department team limit enforced")


class TestOrganization:
    """Tests for Organization."""
    
    def test_create_organization(self):
        """Test organization creation."""
        from services.orchestrator.core.organization import Organization
        
        org = Organization()
        
        assert org.total_agents == 0
        assert len(org.list_departments()) == 0
        
        print("\n✅ Organization created")
    
    def test_full_hierarchy(self):
        """Test full org hierarchy creation."""
        from services.orchestrator.core.organization import (
            Organization, Domain, Role, RoleType
        )
        
        org = Organization()
        
        # Create departments
        research = org.create_department("Research", Domain.RESEARCH)
        finance = org.create_department("Finance", Domain.FINANCE)
        
        # Add teams
        market_team = research.add_team("Market Analysis", max_agents=3)
        quant_team = finance.add_team("Quantitative", max_agents=5)
        
        # Add agents
        analyst_role = Role("Analyst", RoleType.ANALYST, "Analyze data")
        
        market_team.add_agent(analyst_role)
        market_team.add_agent(analyst_role)
        quant_team.add_agent(analyst_role)
        
        # Check stats
        stats = org.stats
        
        assert stats["departments"] == 2
        assert stats["total_agents"] == 3
        assert stats["by_domain"]["research"] == 2
        assert stats["by_domain"]["finance"] == 1
        
        print(f"\n✅ Full hierarchy works: {stats}")
    
    def test_get_organization_singleton(self):
        """Test singleton pattern."""
        from services.orchestrator.core.organization import get_organization
        
        org1 = get_organization()
        org2 = get_organization()
        
        assert org1 is org2
        
        print("\n✅ Singleton pattern works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
