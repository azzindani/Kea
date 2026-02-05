"""
Planner Node.

Decomposes research queries into sub-queries, hypotheses, and EXECUTION PLANS.
Each micro-task is routed to specific tools with dependencies and fallbacks.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole
import asyncio

logger = get_logger(__name__)


# ============================================================================
# Execution Plan Schema
# ============================================================================

class MicroTask(BaseModel):
    """A single micro-task in the execution plan."""
    task_id: str
    description: str
    tool: str  # Which tool to call
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)  # task_ids this depends on
    fallback_tools: list[str] = Field(default_factory=list)  # If primary fails
    persist: bool = True  # Always persist by default (high threshold policy)
    phase: str = "research"  # Execution phase for parallel batching

    # Node Assembly Engine fields
    input_mapping: dict[str, str] = Field(default_factory=dict)  # {"csv_path": "{{step_id.artifacts.key}}"}
    output_artifact: str | None = None  # Artifact key this task produces

    # Workflow node type (tool, code, llm, switch, loop, merge, agentic)
    node_type: str = "tool"

    # Advanced node fields (stored as raw dict for DAG executor to interpret)
    node_config: dict[str, Any] = Field(default_factory=dict)
    
    
class ExecutionPlan(BaseModel):
    """Full execution plan for a research query."""
    plan_id: str
    query: str
    micro_tasks: list[MicroTask] = Field(default_factory=list)
    phases: list[str] = Field(default_factory=list)  # Phase names
    estimated_tools: int = 0
    

# ============================================================================
# Tool Routing Logic
# ============================================================================

from services.orchestrator.core.tool_loader import route_to_tool_dynamic

def route_to_tool(task_description: str) -> tuple[str, list[str]]:
    """
    Route a micro-task to the appropriate tool based on keywords.
    Delegates to dynamic loader.
    """
    return route_to_tool_dynamic(task_description)


def _extract_template_variables(query: str, expected_vars: list[str]) -> dict[str, str]:
    """
    Extract variable values from query for template expansion.
    
    Uses pattern matching to find common variable types:
    - ticker: Stock symbols like BBCA.JK, NVDA, AAPL
    - company: Company names
    - period: Time periods like 1y, 6mo, 3mo
    
    Args:
        query: User's research query
        expected_vars: List of variable names the template expects
        
    Returns:
        Dict of variable name -> extracted value
    """
    import re
    
    variables = {}
    query_upper = query.upper()
    
    for var in expected_vars:
        if var.lower() == "ticker":
            # Look for stock ticker patterns (e.g., BBCA.JK, NVDA, AAPL)
            ticker_match = re.search(r'\b([A-Z]{1,5}(?:\.[A-Z]{1,3})?)\b', query_upper)
            if ticker_match:
                variables[var] = ticker_match.group(1)
            else:
                # Default to first word as ticker
                words = query.split()
                variables[var] = words[0].upper() if words else "AAPL"
                
        elif var.lower() == "company":
            # Use first few words as company name
            words = query.split()[:3]
            variables[var] = " ".join(words)
            
        elif var.lower() == "period":
            # Look for period patterns (1y, 6mo, 3mo, 1d, etc.)
            period_match = re.search(r'\b(\d+(?:y|mo|d|w))\b', query.lower())
            if period_match:
                variables[var] = period_match.group(1)
            else:
                variables[var] = "1y"  # Default
                
        elif var.lower() in ("source_url", "url"):
            # Look for URL patterns
            url_match = re.search(r'https?://[^\s]+', query)
            if url_match:
                variables[var] = url_match.group(0)
            else:
                variables[var] = query  # Use query as source
                
        elif var.lower() in ("output_format", "format"):
            # Look for format mentions
            if "json" in query.lower():
                variables[var] = "json"
            elif "csv" in query.lower():
                variables[var] = "csv"
            elif "markdown" in query.lower() or "md" in query.lower():
                variables[var] = "markdown"
            else:
                variables[var] = "json"  # Default
                
        elif var.lower() == "document_type":
            # Legal document types
            for doc_type in ["10-K", "10-Q", "8-K", "contract", "agreement", "filing"]:
                if doc_type.lower() in query.lower():
                    variables[var] = doc_type
                    break
            else:
                variables[var] = "filing"
                
        else:
            # Generic: use query as the variable value
            variables[var] = query
            
    return variables


# ============================================================================
# Planner Node
# ============================================================================

async def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Planner node: Decompose query into sub-queries AND execution plan.
    
    Takes a complex research query and breaks it down into:
    - Sub-queries (atomic research questions)
    - Hypotheses (testable claims)
    - Execution plan (micro-tasks with tool routing)
    
    Args:
        state: Current graph state with 'query'
        
    Returns:
        Updated state with 'sub_queries', 'hypotheses', 'execution_plan'
    """
    logger.info("Planner: Decomposing query", extra={"query": state.get("query", "")[:100]})
    
    query = state.get("query", "")
    
    # ============================================================
    # RELATED FACT LOOKUP (Semantic Search for Past Research)
    # ============================================================
    related_facts = []
    try:
        import asyncio
        from services.rag_service.core.fact_store import FactStore
        from shared.hardware.detector import detect_hardware
        
        store = FactStore()
        hw = detect_hardware()
        fact_limit = hw.optimal_fact_limit()  # Hardware-aware limit
        
        # Search for related past research with timeout to avoid blocking
        related_facts = await asyncio.wait_for(
            store.search(query, limit=fact_limit),
            timeout=5.0  # 5 second timeout to avoid blocking research
        )
        
        if related_facts:
            logger.info(f"Planner: Found {len(related_facts)} related past facts")
            state["related_facts"] = [
                {"entity": f.entity, "value": f.value[:200], "source": f.source_url}
                for f in related_facts
            ]
    except asyncio.TimeoutError:
        logger.warning("Planner: Related fact lookup timed out, skipping")
    except Exception as e:
        logger.debug(f"Related fact lookup skipped: {e}")
    
    # ============================================================
    # COMPLEXITY CLASSIFICATION (Dynamic Limit Scaling)
    # ============================================================
    try:
        from services.orchestrator.core.complexity import classify_complexity
        complexity = classify_complexity(query)
        state["complexity"] = {
            "tier": complexity.tier.value,
            "entity_count": complexity.entity_count,
            "composite": complexity.composite,
            "max_subtasks": complexity.max_subtasks,
            "max_phases": complexity.max_phases,
            "max_depth": complexity.max_depth,
            "max_parallel": complexity.max_parallel,
            "max_research_iterations": complexity.max_research_iterations,
        }
    except Exception as e:
        logger.warning(f"Complexity classification failed: {e}")
        complexity = None

    # Use LLM to decompose query
    try:
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            provider = OpenRouterProvider()
            from shared.config import get_settings
            app_config = get_settings()
            
            config = LLMConfig(
                model=app_config.models.planner_model,
                temperature=0.3,
                max_tokens=32768,  # Maximum for task generation
            )
            
            # ============================================================
            # TEMPLATE-FIRST PLANNING (Node Assembly Engine)
            # ============================================================
            # Check for matching templates before calling LLM
            # This reduces hallucination for common workflows
            template_used = False
            try:
                from services.orchestrator.templates.loader import get_template_loader
                loader = get_template_loader()
                
                matched_template = loader.match(query)
                if matched_template:
                    template = loader.load(matched_template)
                    if template:
                        logger.info(f"🎯 Using template: {matched_template}")
                        
                        # Extract variables from query
                        variables = _extract_template_variables(query, template.get("variables", []))
                        
                        # Expand template into tasks
                        expanded_tasks = loader.expand(template, variables)
                        
                        # Generate execution plan from expanded template
                        execution_plan = generate_execution_plan_from_blueprint(
                            query, 
                            {"blueprint": expanded_tasks}
                        )
                        
                        state["sub_queries"] = [query]
                        state["hypotheses"] = []
                        state["execution_plan"] = execution_plan.model_dump()
                        state["status"] = "planning_complete"
                        state["template_used"] = matched_template
                        
                        logger.info(
                            f"Planner: Generated {len(execution_plan.micro_tasks)} tasks "
                            f"from template: {matched_template}"
                        )
                        template_used = True
                        
            except Exception as e:
                logger.warning(f"Template matching failed: {e}. Falling back to LLM.")
            
            # If template was used, skip LLM planning
            if template_used:
                return state
            
            # Discover relevant tools (INTELLIGENCE INJECTION - RAG)
            try:
                from services.mcp_host.core.session_registry import get_session_registry
                registry = get_session_registry()
                
                # 1. Try High-Limit Semantic Search (RAG)
                # This scales to 10k+ tools by finding only relevant ones
                relevant_tools = []
                try:
                    # Search specifically for tools that match the query intention
                    search_results = await asyncio.wait_for(
                        registry.search_tools(query, limit=50),  # Reduced limit for schema inclusion
                        timeout=5.0
                    )
                    
                    if search_results:
                        logger.info(f"Planner: RAG found {len(search_results)} relevant tools")
                        # Format: "tool_name: {input_schema}" for precise mapping
                        for t in search_results:
                            name = t.get('name', 'N/A')
                            desc = t.get('description', '')[:200]
                            schema = t.get('inputSchema', {})
                            # Compact schema representation
                            schema_str = str(schema).replace("{", "{{").replace("}", "}}")
                            relevant_tools.append(f"TOOL: {name}\nDESCRIPTION: {desc}\nSCHEMA: {schema_str}\n")
                except Exception as search_err:
                    logger.warning(f"Planner RAG Search failed: {search_err}. Falling back to active list.")

                # 2. Fallback: List Active/Cached Tools (Safety Net)
                if not relevant_tools:
                    if registry.tool_to_server:
                        known_tools = list(registry.tool_to_server.keys())
                        # Slice to avoid context overflow
                        target_tools = known_tools[:100]
                        logger.info(f"Planner: Using fallback list of {len(target_tools)} tools")
                        
                        # We need schemas for these tools. Attempt to fetch if possible, 
                        # otherwise fall back to name:desc.
                        # Since we can't easily fetch schemas for 100 tools quickly without RAG,
                        # we might process them in batches or accept lower fidelity here.
                        # For now, let's try to get schemas for the first 20 most likely relevant?
                        # Or just list them.
                        
                        # HEURISTIC: Just list names for fallback to avoid latency spike
                        relevant_tools = [f"TOOL: {t}" for t in target_tools]
                    else:
                        # 3. Last Resort: Try to force discovery once
                        try:
                            logger.info("Planner: Registry empty, forcing tool scan...")
                            all_tools = await asyncio.wait_for(registry.list_all_tools(), timeout=5.0)
                            # Here we HAVE schemas
                            for t in all_tools[:50]:
                                name = t.get('name', 'N/A')
                                desc = t.get('description', '')[:100]
                                schema = t.get('inputSchema', {})
                                schema_str = str(schema).replace("{", "{{").replace("}", "}}")
                                relevant_tools.append(f"TOOL: {name}\nDESCRIPTION: {desc}\nSCHEMA: {schema_str}\n")
                        except asyncio.TimeoutError:
                             pass

                # Format for LLM
                if relevant_tools:
                    tools_context = f"RELEVANT TOOLS ({len(relevant_tools)} found):\n"
                    tools_context += "\n".join(relevant_tools)
                else:
                    tools_context = "No specific tools found. Rely on 'web_search' and 'execute_code'."
                
            except Exception as e:
                logger.warning(f"Planner tool discovery CRITICAL FAILURE: {e}")
                tools_context = "Tool Discovery Unavailable."

            # Complexity-aware planning guidance
            complexity_guidance = ""
            if complexity:
                complexity_guidance = f"""
QUERY COMPLEXITY: {complexity.tier.value.upper()}
- Entities detected: {complexity.entity_count}
- Recommended steps: {complexity.max_subtasks}
- Maximum phases: {complexity.max_phases}
- Scale the blueprint to match this complexity. Simple queries need 2-3 steps.
  Complex queries with many entities need {complexity.max_subtasks}+ steps.
  Generate as many steps as the query ACTUALLY requires — do NOT default to 3."""

            # JSON Blueprint System Prompt (Level 30 Architect)
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=f"""ACT AS: Execution Architect for Kea (Autonomous Research Engine).
OBJECTIVE: Convert user intent into an executable JSON Blueprint with PRECISE INPUT MAPPING.
{complexity_guidance}

AVAILABLE TOOLS:
{tools_context}

CRITICAL RULES:
1. OUTPUT ONLY JSON. No prose, no explanations.
2. SELECTIVITY: Use only the tools necessary to answer the user query.
3. DEPENDENCIES: Tasks with same "phase" run in parallel. Higher phase waits for lower phases.
4. ARTIFACTS: Use "artifact" to assign a variable name to each step's output (e.g., "csv_file", "search_results").
5. INPUT MAPPING (The Core Mechanic):
   - You MUST map outputs from previous steps to inputs of subsequent steps using `input_mapping`.
   - Syntax: `{{{{step_id.artifacts.artifact_name}}}}` refers to the output of `step_id`.
   - Deep Selection: You can access JSON fields or array items:
     - `{{{{s1.artifacts.data.items[0].id}}}}` (First item's ID)
     - `{{{{s1.artifacts.data.items[*].price}}}}` (List of all prices)
   - Schema Compliance: Ensure mapped values match the TOOL SCHEMA provided above.
   - Example: if `calculate_indicators` needs `csv_path`, map it: `"input_mapping": {{{{"csv_path": "{{{{s1.artifacts.prices_csv}}}}"}}}}`.

6. ADVANCED NODE TYPES:
   - "type": "loop" -> Iterate over a list.
     - `loop_over`: `{{{{step.artifacts.list}}}}`
     - `loop_body`: List of steps to run for each item. Use `{{{{loop_variable}}}}` (default `item`) in args.
   - "type": "switch" -> Conditional logic.
     - `condition`: `len({{{{s1.artifacts.data}}}}) > 0`
   - "type": "merge" -> Combine results.
     - `merge_inputs`: ["s1", "s2"]

OUTPUT SCHEMA:
{{{{
  "intent": "Brief technical summary",
  "blueprint": [
    {{{{
      "id": "step_1",
      "phase": 1,
      "tool": "yfinance_server.get_bulk_historical_data",
      "args": {{{{"tickers": "BBCA.JK", "period": "1y"}}}},
      "artifact": "prices_csv"
    }}}},
    {{{{
      "id": "step_2",
      "phase": 2,
      "tool": "pandas_ta_server.calculate_indicators",
      "args": {{{{"indicators": ["rsi", "macd"]}}}},
      "input_mapping": {{{{"csv_path": "{{{{step_1.artifacts.prices_csv}}}}"}}}},
      "artifact": "indicators"
    }}}}
  ]
}}}}"""
                ),
                LLMMessage(role=LLMRole.USER, content=query)
            ]
            
            response = await provider.complete(messages, config)
            
            # Parse JSON Blueprint response
            blueprint = None
            try:
                import json
                import re
                
                # Extract JSON from response (handle markdown code blocks)
                content = response.content.strip()
                
                # Try to find JSON in code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\})\s*```', content)
                if json_match:
                    content = json_match.group(1)
                # Or find raw JSON object
                elif content.startswith('{'):
                    pass  # Already JSON
                else:
                    # Try to find JSON anywhere in response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        content = content[json_start:json_end]
                
                blueprint = json.loads(content)
                logger.info(f"Planner: Parsed JSON Blueprint with {len(blueprint.get('blueprint', []))} steps")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Planner: JSON parse failed ({e}), falling back to text parsing")
                blueprint = None
            
            if blueprint and "blueprint" in blueprint:
                # Generate execution plan from JSON Blueprint
                execution_plan = generate_execution_plan_from_blueprint(query, blueprint)
                state["execution_plan"] = execution_plan.model_dump()
                state["sub_queries"] = [blueprint.get("intent", query)]
                state["hypotheses"] = []
                
                logger.info(
                    f"Planner: Generated {len(execution_plan.micro_tasks)} micro-tasks "
                    f"across {len(execution_plan.phases)} phases from JSON Blueprint"
                )
            else:
                # Fallback: Parse as text (legacy compatibility)
                sub_queries = []
                hypotheses = []
                execution_phases = {}
                current_phase_name = "default"
                
                lines = response.content.split("\n")
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if "SUB-QUERIES" in line.upper():
                        current_section = "sub_queries"
                        continue
                    elif "HYPOTHESES" in line.upper():
                        current_section = "hypotheses"
                        continue
                    elif "PHASE:" in line.upper():
                        current_section = "execution"
                        try:
                            current_phase_name = line.split(":", 1)[1].strip().lower()
                        except:
                            current_phase_name = "unknown"
                        if current_phase_name not in execution_phases:
                            execution_phases[current_phase_name] = []
                        continue
                    
                    # Extract content
                    text = None
                    if line[0].isdigit() and "." in line:
                        text = line.split(".", 1)[1].strip()
                    elif line.startswith(("-", "*", "•")):
                        text = line[1:].strip()
                    elif current_section == "execution" and len(line) > 10:
                        text = line
                    
                    if text and current_section:
                        if current_section == "sub_queries":
                            sub_queries.append(text)
                        elif current_section == "hypotheses":
                            hypotheses.append(text)
                        elif current_section == "execution":
                            if current_phase_name not in execution_phases:
                                execution_phases[current_phase_name] = []
                            execution_phases[current_phase_name].append(text)
                
                state["sub_queries"] = sub_queries or [query]
                state["hypotheses"] = hypotheses
                
                execution_plan = generate_execution_plan_phased(query, execution_phases)
                state["execution_plan"] = execution_plan.model_dump()
                
                logger.info(
                    f"Planner: Generated {len(execution_plan.micro_tasks)} micro-tasks "
                    f"(text fallback mode)"
                )
            
        else:
            # Fallback without LLM
            state["sub_queries"] = [query]
            state["hypotheses"] = []
            state["execution_plan"] = generate_execution_plan_phased(query, {"research": [query]}).model_dump()
            logger.info("Planner: No LLM, using query as-is")
            
    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["sub_queries"] = [query]
        state["hypotheses"] = []
        state["execution_plan"] = generate_execution_plan_phased(query, {"research": [query]}).model_dump()
    
    state["status"] = "planning_complete"
    return state


def generate_execution_plan_phased(query: str, execution_phases: dict[str, list[str]]) -> ExecutionPlan:
    """
    Generate execution plan from Phased LLM output.
    
    STRICT DEPENDENCY LOGIC:
    - All tasks in Phase N depend on ALL tasks in Phase N-1.
    - Tasks within the same Phase are independent (Parallel).
    """
    import uuid
    
    micro_tasks = []
    task_id_counter = 1
    
    # Track tasks by phase for dependency linking
    # We maintain order of phases as they appeared in the dict (insertion order preserved in Py3.7+)
    phase_names = list(execution_phases.keys())
    phase_task_ids: dict[str, list[str]] = {p: [] for p in phase_names}
    
    for i, phase_name in enumerate(phase_names):
        steps = execution_phases[phase_name]
        
        # Determine dependencies: All tasks from previous phase
        depends_on = []
        if i > 0:
            previous_phase = phase_names[i-1]
            depends_on = phase_task_ids[previous_phase]
            
        for step in steps:
            task_id = f"task_{task_id_counter}"
            task_id_counter += 1
            
            primary_tool, fallbacks = route_to_tool(step)
            
            # Handle special case: execute_code needs "python_server" usually
            # route_to_tool logic might need checking, but usually returns 'execute_code'
            
            micro_task = MicroTask(
                task_id=task_id,
                description=step,
                tool=primary_tool,
                inputs={"query": step},  # Basic input, refined by researcher_node
                depends_on=depends_on,   # STRICT DEPENDENCY
                fallback_tools=fallbacks,
                persist=True,
                phase=phase_name,
            )
            
            micro_tasks.append(micro_task)
            phase_task_ids[phase_name].append(task_id)
            
    return ExecutionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        query=query,
        micro_tasks=micro_tasks,
        phases=phase_names,
        estimated_tools=len(micro_tasks),
    )


def generate_execution_plan_from_blueprint(query: str, blueprint: dict) -> ExecutionPlan:
    """
    Generate execution plan from JSON Blueprint (new format).
    
    Blueprint format:
    {
        "intent": "short description",
        "blueprint": [
            {"id": "s1", "phase": 1, "tool": "web_search", "args": {...}, "artifact": "key"},
            ...
        ]
    }
    """
    import uuid
    
    micro_tasks = []
    steps = blueprint.get("blueprint", [])
    
    # Group steps by phase for dependency calculation
    phase_map: dict[int, list[str]] = {}  # phase_number -> [step_ids]
    
    for step in steps:
        phase_num = step.get("phase", 1)
        step_id = step.get("id", f"step_{len(micro_tasks) + 1}")
        if phase_num not in phase_map:
            phase_map[phase_num] = []
        phase_map[phase_num].append(step_id)
    
    # Sort phases to build dependency chain
    sorted_phases = sorted(phase_map.keys())
    
    for step in steps:
        step_id = step.get("id", f"step_{len(micro_tasks) + 1}")
        phase_num = step.get("phase", 1)
        tool_name = step.get("tool", "execute_code")
        args = step.get("args", {})
        artifact_key = step.get("artifact")
        
        # Calculate dependencies: all steps from previous phase
        depends_on = []
        phase_idx = sorted_phases.index(phase_num)
        if phase_idx > 0:
            previous_phase = sorted_phases[phase_idx - 1]
            depends_on = phase_map.get(previous_phase, [])
        
        # Build inputs from args
        inputs = {}
        for key, value in args.items():
            inputs[key] = value
        
        # Parse input_mapping from blueprint (Node Assembly Engine)
        input_mapping = step.get("input_mapping", {})

        # Detect node type from step
        node_type = step.get("type", "tool")
        if not node_type or node_type == "tool":
            if tool_name in ("execute_code", "run_python"):
                node_type = "code"

        # Collect advanced node config for DAG executor
        node_config: dict[str, Any] = {}
        for adv_key in (
            "condition", "true_branch", "false_branch", "true", "false",
            "loop_over", "over", "loop_body", "body", "loop_variable",
            "merge_inputs", "merge_strategy",
            "goal", "agent_max_steps", "agent_tools", "max_steps", "tools",
            "llm_prompt", "llm_system", "prompt", "system",
            "max_parallel",
        ):
            if adv_key in step:
                node_config[adv_key] = step[adv_key]

        micro_task = MicroTask(
            task_id=step_id,
            description=step.get("description", f"{tool_name}: {args.get('query', args.get('code', str(args)[:100]))}"),
            tool=tool_name,
            inputs=inputs,
            depends_on=step.get("depends_on", depends_on),
            fallback_tools=["execute_code"] if tool_name != "execute_code" else [],
            persist=True,
            phase=str(phase_num),
            input_mapping=input_mapping,
            output_artifact=artifact_key,
            node_type=node_type,
            node_config=node_config,
        )
        
        micro_tasks.append(micro_task)
    
    # Generate phase names from numbers
    phase_names = [str(p) for p in sorted_phases]
    
    return ExecutionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        query=query,
        micro_tasks=micro_tasks,
        phases=phase_names,
        estimated_tools=len(micro_tasks),
    )
