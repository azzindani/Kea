"""
Agentic Workflow Engine for Autonomous Task Execution.

Implements a human-like back-and-forth reasoning loop where the LLM:
1. Analyzes the current state
2. Decides what to do next
3. Executes tools
4. Inspects results
5. Repeats until task is complete

Key Features:
- Dynamic tool selection based on context
- Schema learning from execution
- Self-correcting execution with retries
- Human-like reasoning chain
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from shared.knowledge.retriever import get_knowledge_retriever
from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.mcp.schema_inferrer import get_schema_inferrer
from shared.mcp.schema_registry import SchemaRegistry, get_schema_registry
from shared.prompts import get_agent_prompt

logger = get_logger(__name__)


class AgentAction(str, Enum):
    """Actions the agent can take."""

    CALL_TOOL = "call_tool"  # Execute a tool
    ANALYZE = "analyze"  # Analyze current data
    SYNTHESIZE = "synthesize"  # Create final output
    ASK_CLARIFICATION = "ask_clarification"  # Need more info
    COMPLETE = "complete"  # Task done


@dataclass
class ToolExecution:
    """Record of a single tool execution."""

    tool_name: str
    arguments: dict[str, Any]
    result: Any
    success: bool
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReasoningStep:
    """A single step in the agent's reasoning chain."""

    step_number: int
    thought: str  # What the agent is thinking
    action: AgentAction  # What it decided to do
    action_input: dict  # Input to the action
    observation: str  # Result/observation
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """
    State for the agentic workflow.

    Tracks the full context including:
    - Original query
    - Reasoning chain
    - Tool executions
    - Accumulated data
    """

    query: str = Field(description="Original user query")
    objective: str = Field(default="", description="Refined objective")

    # Reasoning chain
    reasoning_steps: list[dict] = Field(default_factory=list)
    current_step: int = Field(default=0)
    max_steps: int = Field(default=15)

    # Tool execution history
    tool_executions: list[dict] = Field(default_factory=list)

    # Accumulated data/artifacts
    artifacts: dict[str, Any] = Field(default_factory=dict)

    # Status
    status: str = Field(default="thinking")
    final_answer: str = Field(default="")
    error: str | None = Field(default=None)

    # Schema learning
    learned_schemas: list[str] = Field(default_factory=list)


class AgenticWorkflow:
    """
    Autonomous workflow engine with human-like reasoning.

    Implements a ReAct-style loop:
    1. Thought: Reason about current state
    2. Action: Decide what to do
    3. Observation: Execute and observe result
    4. Repeat until done

    Example:
        workflow = AgenticWorkflow(tool_executor)
        result = await workflow.run("Analyze TSLA financials")

        # The agent will:
        # 1. Think: "I need to get TSLA's financial data..."
        # 2. Call: yfinance_server.get_income_statement_quarterly
        # 3. Observe: "Got income statement with revenue, net income..."
        # 4. Think: "Now I should analyze the trends..."
        # 5. Call: python_server.execute (analysis code)
        # 6. ... continue until complete
    """

    def __init__(
        self,
        tool_executor: Callable[[str, dict], Awaitable[Any]],
        schema_registry: SchemaRegistry | None = None,
        model: str | None = None,
        max_steps: int = 15,
    ):
        """
        Initialize the agentic workflow.

        Args:
            tool_executor: Async function to execute tools (name, args) -> result
            schema_registry: Registry for schema learning
            model: LLM model to use
            max_steps: Maximum reasoning steps
        """
        self.tool_executor = tool_executor
        self.registry = schema_registry or get_schema_registry()
        self.inferrer = get_schema_inferrer()
        self.max_steps = max_steps

        # LLM setup
        from shared.config import get_settings

        settings = get_settings()
        self.model = model or settings.models.planner_model
        self.provider = OpenRouterProvider()

    async def run(
        self,
        query: str,
        available_tools: list[dict] | None = None,
        initial_context: dict | None = None,
    ) -> AgentState:
        """
        Run the agentic workflow for a query.

        Args:
            query: User's query/objective
            available_tools: List of available tool definitions
            initial_context: Optional starting context

        Returns:
            Final AgentState with results
        """
        state = AgentState(query=query, max_steps=self.max_steps, artifacts=initial_context or {})

        logger.info(f"  Starting agentic workflow: {query[:100]}")

        # Discover available tools if not provided
        if available_tools is None:
            available_tools = await self._discover_tools(query)

        # Main reasoning loop
        while state.current_step < state.max_steps:
            state.current_step += 1

            try:
                # Get next action from LLM
                thought, action, action_input = await self._reason(state, available_tools)

                # Record the reasoning step
                step = {
                    "step": state.current_step,
                    "thought": thought,
                    "action": action.value,
                    "action_input": action_input,
                    "observation": "",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                logger.info(f"  Step {state.current_step}: {thought[:100]}...")
                logger.info(f"  Action: {action.value}")

                # Execute the action
                if action == AgentAction.COMPLETE:
                    state.final_answer = action_input.get("answer", "")
                    state.status = "complete"
                    step["observation"] = "Task completed"
                    state.reasoning_steps.append(step)
                    break

                elif action == AgentAction.CALL_TOOL:
                    observation = await self._execute_tool(
                        state, action_input.get("tool"), action_input.get("arguments", {})
                    )
                    step["observation"] = observation[:500]  # Truncate for logging

                elif action == AgentAction.ANALYZE:
                    observation = await self._analyze(state, action_input)
                    step["observation"] = observation[:500]

                elif action == AgentAction.SYNTHESIZE:
                    state.final_answer = await self._synthesize(state, action_input)
                    state.status = "complete"
                    step["observation"] = "Synthesis complete"
                    state.reasoning_steps.append(step)
                    break

                state.reasoning_steps.append(step)

            except Exception as e:
                logger.error(f"  Error in step {state.current_step}: {e}")
                state.reasoning_steps.append(
                    {
                        "step": state.current_step,
                        "thought": "Error occurred",
                        "action": "error",
                        "observation": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                # Continue to next step, let LLM handle recovery

        if state.status != "complete":
            state.status = "max_steps_reached"
            state.final_answer = await self._force_synthesis(state)

        logger.info(f"  Workflow complete after {state.current_step} steps")
        return state

    async def _reason(
        self, state: AgentState, available_tools: list[dict]
    ) -> tuple[str, AgentAction, dict]:
        """
        LLM reasoning step to decide next action.

        Returns:
            (thought, action, action_input)
        """
        # Build context from state
        context = self._build_context(state, available_tools)

        # Retrieve domain knowledge to enrich reasoning
        knowledge_context = ""
        try:
            knowledge_context = await get_knowledge_retriever().retrieve_skills(state.query)
            if knowledge_context:
                logger.info(
                    f"AgenticWorkflow._reason: injected {len(knowledge_context)} chars of domain knowledge"
                )
            else:
                logger.debug("AgenticWorkflow._reason: No domain knowledge retrieved")
        except Exception as _kr_err:
            logger.debug(f"AgenticWorkflow._reason: knowledge retrieval skipped ({_kr_err})")

        config = LLMConfig(
            model=self.model,
            temperature=0.3,
            max_tokens=32768,
        )

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=self._get_system_prompt(available_tools, knowledge_context),
            ),
            LLMMessage(role=LLMRole.USER, content=context),
        ]

        response = await self.provider.complete(messages, config)

        # Parse the response
        return self._parse_reasoning(response.content)

    def _get_system_prompt(self, available_tools: list[dict], knowledge_context: str = "") -> str:
        """Generate system prompt for the agent."""
        tool_descriptions = "\n".join(
            [
                f"- {t.get('name')}: {t.get('description', '')[:100]}"
                for t in available_tools[:50]  # Limit to avoid context overflow
            ]
        )

        prompt = get_agent_prompt("agentic_step").format(tool_descriptions=tool_descriptions)
        if knowledge_context:
            prompt += f"\n\n{knowledge_context}"
        return prompt

    def _build_context(self, state: AgentState, available_tools: list[dict]) -> str:
        """Build context string for the LLM."""
        # Format previous steps
        history = ""
        for step in state.reasoning_steps[-5:]:  # Last 5 steps for context
            history += f"\n[Step {step['step']}]\n"
            history += f"Thought: {step['thought']}\n"
            history += f"Action: {step['action']}\n"
            if step.get("observation"):
                history += f"Observation: {step['observation'][:300]}...\n"

        # Format artifacts
        artifacts_summary = ""
        for key, value in list(state.artifacts.items())[:5]:
            if isinstance(value, str) and len(value) > 200:
                artifacts_summary += f"\n- {key}: (data with {len(value)} chars)"
            else:
                artifacts_summary += f"\n- {key}: {str(value)[:100]}"

        return f"""OBJECTIVE: {state.query}

STEP: {state.current_step + 1} of {state.max_steps}

PREVIOUS STEPS:{history if history else " None yet"}

COLLECTED DATA:{artifacts_summary if artifacts_summary else " None yet"}

What should I do next? Respond with JSON only."""

    def _parse_reasoning(self, content: str) -> tuple[str, AgentAction, dict]:
        """Parse LLM response into thought, action, and input."""
        try:
            # Try to extract JSON
            content = content.strip()

            # Handle markdown code blocks
            if "```" in content:
                import re

                json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
                if json_match:
                    content = json_match.group(1)

            # Find JSON object
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]

            data = json.loads(content)

            thought = data.get("thought", "Thinking...")
            action_str = data.get("action", "analyze")
            action_input = data.get("action_input", {})

            # Map action string to enum
            action_map = {
                "call_tool": AgentAction.CALL_TOOL,
                "analyze": AgentAction.ANALYZE,
                "synthesize": AgentAction.SYNTHESIZE,
                "complete": AgentAction.COMPLETE,
            }
            action = action_map.get(action_str, AgentAction.ANALYZE)

            return thought, action, action_input

        except Exception as e:
            logger.warning(f"Failed to parse reasoning: {e}")
            # Default to analysis
            return content[:200], AgentAction.ANALYZE, {}

    async def _execute_tool(self, state: AgentState, tool_name: str, arguments: dict) -> str:
        """Execute a tool and learn from the result."""
        logger.info(f"  Executing: {tool_name}")

        start_time = datetime.utcnow()

        try:
            result = await self.tool_executor(tool_name, arguments)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Record execution
            execution = {
                "tool": tool_name,
                "arguments": arguments,
                "success": True,
                "duration_ms": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }
            state.tool_executions.append(execution)

            # Learn schema from result
            if "." in tool_name:
                server, tool = tool_name.rsplit(".", 1)
                schema = self.registry.register_from_result(tool, server, result)
                if schema.full_name not in state.learned_schemas:
                    state.learned_schemas.append(schema.full_name)
                    logger.info(f"  Learned schema for {schema.full_name}")

            # Store result as artifact
            artifact_key = f"result_{len(state.tool_executions)}"
            state.artifacts[artifact_key] = result

            # Return observation for LLM
            if isinstance(result, str):
                return result[:1000]  # Truncate long results
            else:
                return json.dumps(result, default=str)[:1000]

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            state.tool_executions.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return f"ERROR: {e}"

    async def _analyze(self, state: AgentState, input_data: dict) -> str:
        """Have LLM analyze current data."""
        config = LLMConfig(
            model=self.model,
            temperature=0.2,
            max_tokens=2048,
        )

        # Collect data to analyze
        data_to_analyze = input_data.get("data", "")
        if not data_to_analyze:
            # Use recent artifacts
            recent_results = [
                state.artifacts.get(f"result_{i + 1}", "")
                for i in range(len(state.tool_executions))
            ][-3:]  # Last 3 results
            data_to_analyze = "\n---\n".join(str(r)[:500] for r in recent_results if r)

        # Retrieve analysis-relevant knowledge
        knowledge_context = ""
        try:
            knowledge_context = await get_knowledge_retriever().retrieve_skills(state.query)
            if knowledge_context:
                logger.info(
                    f"AgenticWorkflow._analyze: injected {len(knowledge_context)} chars of domain knowledge"
                )
            else:
                logger.debug("AgenticWorkflow._analyze: No domain knowledge retrieved")
        except Exception as _kr_err:
            logger.debug(f"AgenticWorkflow._analyze: knowledge retrieval skipped ({_kr_err})")

        analyzer_prompt = get_agent_prompt("agentic_analyzer")
        if knowledge_context:
            analyzer_prompt += f"\n\n{knowledge_context}"

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=analyzer_prompt),
            LLMMessage(
                role=LLMRole.USER,
                content=f"Query: {state.query}\n\nData:\n{data_to_analyze[:3000]}",
            ),
        ]

        response = await self.provider.complete(messages, config)

        # Store analysis
        state.artifacts["analysis"] = response.content
        return response.content[:500]

    async def _synthesize(self, state: AgentState, input_data: dict) -> str:
        """Synthesize final answer from all gathered data."""
        config = LLMConfig(
            model=self.model,
            temperature=0.3,
            max_tokens=32768,
        )

        # Compile all gathered information
        all_data = []
        for key, value in state.artifacts.items():
            if isinstance(value, str) and len(value) > 50:
                all_data.append(f"[{key}]\n{value[:800]}")

        # Retrieve synthesis-relevant knowledge
        knowledge_context = ""
        try:
            knowledge_context = await get_knowledge_retriever().retrieve_skills(state.query)
            if knowledge_context:
                logger.info(
                    f"AgenticWorkflow._synthesize: injected {len(knowledge_context)} chars of domain knowledge"
                )
            else:
                logger.debug("AgenticWorkflow._synthesize: No domain knowledge retrieved")
        except Exception as _kr_err:
            logger.debug(f"AgenticWorkflow._synthesize: knowledge retrieval skipped ({_kr_err})")

        synthesizer_prompt = get_agent_prompt("agentic_synthesizer")
        if knowledge_context:
            synthesizer_prompt += f"\n\n{knowledge_context}"

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=synthesizer_prompt),
            LLMMessage(
                role=LLMRole.USER,
                content=f"""Original Query: {state.query}

Gathered Data:
{chr(10).join(all_data[:10])}

Provide a complete answer:""",
            ),
        ]

        response = await self.provider.complete(messages, config)
        return response.content

    async def _force_synthesis(self, state: AgentState) -> str:
        """Force a synthesis when max steps reached."""
        logger.warning("Max steps reached, forcing synthesis")
        return await self._synthesize(state, {})

    async def _discover_tools(self, query: str) -> list[dict]:
        """Discover relevant tools for the query."""
        try:
            from kernel.interfaces.tool_registry import get_tool_registry

            registry = get_tool_registry()

            # Search for relevant tools
            tools = await asyncio.wait_for(registry.search_tools(query, limit=50), timeout=5.0)

            if tools:
                return tools

            # Fallback to listing all
            all_tools = await asyncio.wait_for(registry.list_tools(), timeout=5.0)
            return all_tools[:100]

        except Exception as e:
            logger.warning(f"Tool discovery failed: {e}")
            # Return empty list, will rely on LLM knowledge
            return []


# Convenience function
async def run_agentic_workflow(
    query: str, tool_executor: Callable[[str, dict], Awaitable[Any]], **kwargs
) -> AgentState:
    """
    Run an agentic workflow for a query.

    Example:
        async def execute_tool(name: str, args: dict) -> str:
            # Your tool execution logic
            return await mcp_host.call_tool(name, args)

        result = await run_agentic_workflow(
            "Analyze TSLA financials",
            tool_executor=execute_tool
        )
        print(result.final_answer)
    """
    workflow = AgenticWorkflow(tool_executor, **kwargs)
    return await workflow.run(query)
