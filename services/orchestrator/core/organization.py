"""
Organizational Hierarchy for Enterprise-Scale Agent Operations.

Enables 100K employee-equivalent operations with:
- Departments: Domain-specialized agent groups
- Teams: Coordinated agent pools
- Roles: Individual agent capabilities
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from shared.logging import get_logger


logger = get_logger(__name__)


class Domain(str, Enum):
    """Department domains."""
    RESEARCH = "research"
    FINANCE = "finance"
    LEGAL = "legal"
    ENGINEERING = "engineering"
    ANALYTICS = "analytics"
    OPERATIONS = "operations"
    GENERAL = "general"


class RoleType(str, Enum):
    """Agent role types."""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    VALIDATOR = "validator"
    SYNTHESIZER = "synthesizer"
    SUPERVISOR = "supervisor"
    EXECUTOR = "executor"


@dataclass
class Role:
    """
    Agent role with specific capabilities.
    
    Defines what an agent can do and how it behaves.
    """
    name: str
    role_type: RoleType
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=list)
    can_spawn: bool = False      # Can create sub-agents?
    can_escalate: bool = True    # Can escalate to supervisor?
    max_concurrent: int = 1      # Max parallel tasks
    
    def to_dict(self) -> dict:
        """Serialize role."""
        return {
            "name": self.name,
            "role_type": self.role_type.value,
            "allowed_tools": self.allowed_tools,
            "can_spawn": self.can_spawn,
            "can_escalate": self.can_escalate,
        }


@dataclass
class AgentInstance:
    """Running agent instance."""
    agent_id: str
    role: Role
    team_id: str
    status: str = "idle"  # idle, working, blocked, completed
    current_task_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, role: Role, team_id: str) -> "AgentInstance":
        """Create new agent instance."""
        return cls(
            agent_id=f"agent_{uuid.uuid4().hex[:8]}",
            role=role,
            team_id=team_id,
        )


@dataclass
class Team:
    """
    Group of agents working on related tasks.
    
    Teams provide:
    - Work queue management
    - Agent pooling
    - Local coordination
    """
    team_id: str
    name: str
    department_id: str
    max_agents: int = 10
    agents: list[AgentInstance] = field(default_factory=list)
    active_tasks: int = 0
    
    @classmethod
    def create(cls, name: str, department_id: str, max_agents: int = 10) -> "Team":
        """Create new team."""
        return cls(
            team_id=f"team_{uuid.uuid4().hex[:8]}",
            name=name,
            department_id=department_id,
            max_agents=max_agents,
        )
    
    def add_agent(self, role: Role) -> AgentInstance | None:
        """Add agent to team if capacity allows."""
        if len(self.agents) >= self.max_agents:
            logger.warning(f"Team {self.name} at capacity ({self.max_agents})")
            return None
        
        agent = AgentInstance.create(role, self.team_id)
        self.agents.append(agent)
        logger.debug(f"Added agent {agent.agent_id} to team {self.name}")
        return agent
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from team."""
        for i, agent in enumerate(self.agents):
            if agent.agent_id == agent_id:
                self.agents.pop(i)
                logger.debug(f"Removed agent {agent_id} from team {self.name}")
                return True
        return False
    
    def get_idle_agents(self) -> list[AgentInstance]:
        """Get agents available for work."""
        return [a for a in self.agents if a.status == "idle"]
    
    @property
    def utilization(self) -> float:
        """Team utilization (0-1)."""
        if not self.agents:
            return 0.0
        working = sum(1 for a in self.agents if a.status == "working")
        return working / len(self.agents)


@dataclass
class Department:
    """
    Virtual department with domain specialization.
    
    Departments provide:
    - Domain-specific tools and prompts
    - Team management
    - Shared memory namespace
    """
    dept_id: str
    name: str
    domain: Domain
    teams: list[Team] = field(default_factory=list)
    default_tools: list[str] = field(default_factory=list)
    max_teams: int = 10
    
    @classmethod
    def create(cls, name: str, domain: Domain, max_teams: int = 10) -> "Department":
        """Create new department."""
        return cls(
            dept_id=f"dept_{uuid.uuid4().hex[:8]}",
            name=name,
            domain=domain,
            max_teams=max_teams,
        )
    
    def add_team(self, name: str, max_agents: int = 10) -> Team | None:
        """Add team to department."""
        if len(self.teams) >= self.max_teams:
            logger.warning(f"Department {self.name} at team capacity")
            return None
        
        team = Team.create(name, self.dept_id, max_agents)
        self.teams.append(team)
        logger.info(f"Created team '{name}' in department '{self.name}'")
        return team
    
    def get_team(self, team_id: str) -> Team | None:
        """Get team by ID."""
        for team in self.teams:
            if team.team_id == team_id:
                return team
        return None
    
    @property
    def total_agents(self) -> int:
        """Total agents across all teams."""
        return sum(len(t.agents) for t in self.teams)
    
    @property
    def total_capacity(self) -> int:
        """Total agent capacity."""
        return sum(t.max_agents for t in self.teams)


class Organization:
    """
    Top-level organizational structure.
    
    Manages departments, provides global coordination.
    
    Example:
        org = Organization()
        
        # Create department
        research = org.create_department("Research", Domain.RESEARCH)
        
        # Add team
        team = research.add_team("Market Analysis", max_agents=5)
        
        # Add agent
        role = Role("Analyst", RoleType.ANALYST, "You analyze data...")
        agent = team.add_agent(role)
    """
    
    def __init__(self):
        self._departments: dict[str, Department] = {}
        self._created_at = datetime.utcnow()
    
    def create_department(
        self,
        name: str,
        domain: Domain,
        max_teams: int = 10,
    ) -> Department:
        """Create and register a new department."""
        dept = Department.create(name, domain, max_teams)
        self._departments[dept.dept_id] = dept
        logger.info(f"Created department '{name}' ({domain.value})")
        return dept
    
    def get_department(self, dept_id: str) -> Department | None:
        """Get department by ID."""
        return self._departments.get(dept_id)
    
    def get_department_by_domain(self, domain: Domain) -> Department | None:
        """Get first department matching domain."""
        for dept in self._departments.values():
            if dept.domain == domain:
                return dept
        return None
    
    def list_departments(self) -> list[Department]:
        """List all departments."""
        return list(self._departments.values())
    
    @property
    def total_agents(self) -> int:
        """Total agents across organization."""
        return sum(d.total_agents for d in self._departments.values())
    
    @property
    def stats(self) -> dict:
        """Organization statistics."""
        return {
            "departments": len(self._departments),
            "total_agents": self.total_agents,
            "by_domain": {
                d.domain.value: d.total_agents
                for d in self._departments.values()
            },
        }


# Global organization instance
_organization: Organization | None = None


def get_organization() -> Organization:
    """Get or create global organization."""
    global _organization
    if _organization is None:
        _organization = Organization()
    return _organization
