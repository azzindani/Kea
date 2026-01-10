# Orchestrator Service Package
"""
The Brain - Main orchestrator with LangGraph state machine and MCP client.

Components:
- core/: LangGraph state machine and routing logic
- mcp/: MCP client for tool invocation
- nodes/: LangGraph node implementations
- agents/: Specialized worker agents (Generator, Critic, Judge)
- state/: Pydantic state schemas
"""
