"""
Planner Node.

Decomposes research queries into sub-queries, hypotheses, and EXECUTION PLANS.
Each micro-task is routed to specific tools with dependencies and fallbacks.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger

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
    input_mapping: dict[str, str] = Field(
        default_factory=dict
    )  # {"csv_path": "{{step_id.artifacts.key}}"}
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
# Tool Validation & Fuzzy Matching
# ============================================================================


async def _validate_and_correct_tool_names(execution_plan: ExecutionPlan) -> ExecutionPlan:
    """
    Validate tool names from LLM against 2K+ tool registry and auto-correct common hallucinations.

    Common hallucinations:
    - get_balance_sheet   get_balance_sheet_annual
    - get_income_statement   get_income_statement_annual
    - get_financial_ratios   calculate_indicators (closest alternative)

    Args:
        execution_plan: Execution plan with potentially hallucinated tool names

    Returns:
        Execution plan with validated and corrected tool names
    """
    from difflib import get_close_matches

    from kernel.interfaces.tool_registry import get_tool_registry

    registry = get_tool_registry()
    
    if not registry:
        logger.warning("Tool registry not available, skipping validation")
        return execution_plan

    # Get available tools (2K+ tools from RAG)
    # Note: Registry access might be async depending on implementation, 
    # but here we assume the interface is handled.
    # Actually checking the standard implementation...
    # The interface methods are async. We need to await them.
    
    # Wait, the original code accessed .tool_to_server property synchronously in some parts?
    # Original: if not registry.tool_to_server: await registry.list_all_tools()
    # New Interface: await registry.list_tools() returns list of dicts.
    
    tools_list = await registry.list_tools()
    available_tools = {t.get("name") for t in tools_list}

    # Common hallucination aliases
    aliases = {
        "get_balance_sheet": "get_balance_sheet_annual",
        "get_income_statement": "get_income_statement_annual",
        "get_cash_flow": "get_cash_flow_annual",
        "get_cash_flow_statement": "get_cash_flow_statement_annual",
        "get_financial_ratios": "calculate_indicators",
        "get_financials": "get_full_report",
        "search": "web_search",
        "scrape": "fetch_url",
        "scrape_url": "fetch_url",
        "google_search": "web_search",
        "bing_search": "web_search",
    }

    corrected_tasks = []
    removed_count = 0
    corrected_count = 0

    for task in execution_plan.micro_tasks:
        tool_name = task.tool

        # Check if tool exists
        if tool_name in available_tools:
            corrected_tasks.append(task)
            continue

        # Check aliases first (fast lookup)
        if tool_name in aliases:
            corrected_tool = aliases[tool_name]
            if corrected_tool in available_tools:
                logger.warning(f"  Correcting hallucinated tool: {tool_name}   {corrected_tool}")
                task.tool = corrected_tool
                corrected_tasks.append(task)
                corrected_count += 1
                continue

        # Fuzzy match (edit distance for typos)
        matches = get_close_matches(tool_name, available_tools, n=1, cutoff=0.8)

        if matches:
            corrected_tool = matches[0]
            logger.warning(
                f"  Fuzzy-matched tool: {tool_name}   {corrected_tool} "
                f"(similarity: {_similarity_score(tool_name, corrected_tool):.2f})"
            )
            task.tool = corrected_tool
            corrected_tasks.append(task)
            corrected_count += 1
        else:
            # Tool doesn't exist and can't be matched - remove task
            logger.error(
                f"  Tool not found in 2K+ registry: {tool_name}. "
                f"Removing task: {task.description[:100]}"
            )
            removed_count += 1
            # Don't add to corrected_tasks (filtered out)

    logger.info(
        f"  Tool validation complete: "
        f"{len(execution_plan.micro_tasks)}   {len(corrected_tasks)} tasks "
        f"({corrected_count} corrected, {removed_count} removed)"
    )

    # Update execution plan with corrected tasks
    execution_plan.micro_tasks = corrected_tasks
    execution_plan.estimated_tools = len(corrected_tasks)

    return execution_plan


async def _validate_tool_arguments(execution_plan: ExecutionPlan, query: str) -> ExecutionPlan:
    """
    Validate tool arguments against FULL JSON schema (not just required params).

    CRITICAL: Uses Postgres RAG for schemas (NOT list_all_tools() which loads ALL servers!)

    Validates:
    - Required parameters present  
    - Parameter TYPES match (string, int, array, object)  
    - Enum values are valid  
    - Min/max constraints  
    - No extra parameters  
    - Nested object structures  

    Args:
        execution_plan: Execution plan to validate
        query: Original user query for extracting values

    Returns:
        Execution plan with fully validated arguments
    """
    from kernel.interfaces.tool_registry import get_tool_registry

    registry = get_tool_registry()
    if not registry:
        logger.warning("Tool registry not available, skipping schema validation")
        return execution_plan

    # Get tool schemas from Postgres RAG (FAST - doesn't load servers!)
    tool_schemas = {}
    try:
        # Query only the tools we need (not all 2000+)
        for task in execution_plan.micro_tasks:
            tool_name = task.tool
            # Search for this specific tool in RAG
            results = await registry.search_tools(tool_name, limit=1)
            if results:
                tool_schemas[tool_name] = results[0].get("inputSchema", {})
                
    except Exception as e:
        logger.warning(f"Could not fetch tool schemas from RAG: {e}")
        return execution_plan

    logger.info(f"  Validating {len(execution_plan.micro_tasks)} tasks against tool schemas...")

    fixed_tasks = []
    validation_stats = {"passed": 0, "fixed": 0, "failed": 0}

    for task in execution_plan.micro_tasks:
        tool_name = task.tool
        args = task.inputs or {}

        # Get schema for this tool
        schema = tool_schemas.get(tool_name, {})
        if not schema:
            # No schema available, keep as-is but log
            logger.warning(f"    No schema found for {tool_name}, skipping validation")
            fixed_tasks.append(task)
            continue

        # FULL JSON SCHEMA VALIDATION
        validation_result = _validate_against_json_schema(args, schema, tool_name)

        if validation_result["valid"]:
            # Schema validation passed
            logger.info(f"  {tool_name} schema validation passed")
            validation_stats["passed"] += 1
            fixed_tasks.append(task)
            continue

        # Schema validation failed - try to fix
        logger.warning(
            f"    {tool_name} validation failed: {', '.join(validation_result['errors'][:2])}"
        )

        # Fix missing required parameters by extracting from query
        if validation_result["missing_required"]:
            logger.info(f"  Extracting missing params: {validation_result['missing_required']}")
            extracted_args = _extract_params_from_query(
                query, validation_result["missing_required"], schema.get("properties", {})
            )
            if extracted_args:
                logger.info(f"  Extracted: {extracted_args}")
                args = {**args, **extracted_args}
            else:
                logger.warning("  Could not extract params from query")

        # Fix type mismatches
        if validation_result["type_errors"]:
            args = _fix_type_mismatches(args, validation_result["type_errors"], schema)

        # Remove extra parameters
        if validation_result["extra_params"]:
            for extra_param in validation_result["extra_params"]:
                logger.info(f"  Removing extra param '{extra_param}'")
                args.pop(extra_param, None)

        # Update task with fixed args
        task.inputs = args

        # Re-validate after fixes
        revalidation = _validate_against_json_schema(args, schema, tool_name)
        if revalidation["valid"]:
            logger.info(f"  {tool_name} fixed successfully")
            validation_stats["fixed"] += 1
        else:
            logger.error(f"  {tool_name} still invalid: {', '.join(revalidation['errors'][:2])}")
            validation_stats["failed"] += 1

        fixed_tasks.append(task)

    logger.info(
        f"  Validation complete: {validation_stats['passed']} passed, "
        f"{validation_stats['fixed']} fixed, {validation_stats['failed']} failed"
    )

    execution_plan.micro_tasks = fixed_tasks
    return execution_plan


def _validate_against_json_schema(args: dict, schema: dict, tool_name: str) -> dict:
    """
    Validate arguments against JSON schema.

    Returns:
        Dict with validation results:
        {
            'valid': bool,
            'errors': list[str],
            'missing_required': list[str],
            'type_errors': dict,
            'extra_params': list[str]
        }
    """
    result = {
        "valid": True,
        "errors": [],
        "missing_required": [],
        "type_errors": {},
        "extra_params": [],
    }

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    additional_properties = schema.get("additionalProperties", True)

    # Check required parameters
    for param in required:
        if param not in args or args[param] is None or args[param] == "":
            result["valid"] = False
            result["missing_required"].append(param)
            result["errors"].append(f"Missing required: {param}")

    # Check parameter types and constraints
    for param, value in args.items():
        if param not in properties:
            # Extra parameter not in schema
            if not additional_properties:
                result["valid"] = False
                result["extra_params"].append(param)
                result["errors"].append(f"Extra param: {param}")
            continue

        param_schema = properties[param]
        param_type = param_schema.get("type")

        # Type validation
        if param_type:
            type_valid, type_error = _check_type(value, param_type, param)
            if not type_valid:
                result["valid"] = False
                result["type_errors"][param] = {
                    "expected": param_type,
                    "actual": type(value).__name__,
                }
                result["errors"].append(type_error)

        # Enum validation
        if "enum" in param_schema:
            if value not in param_schema["enum"]:
                result["valid"] = False
                result["errors"].append(f"{param}='{value}' not in enum")

        # Min/max validation for numbers
        if param_type in ("integer", "number"):
            if isinstance(value, (int, float)):
                if "minimum" in param_schema and value < param_schema["minimum"]:
                    result["valid"] = False
                    result["errors"].append(f"{param}={value} < min {param_schema['minimum']}")
                if "maximum" in param_schema and value > param_schema["maximum"]:
                    result["valid"] = False
                    result["errors"].append(f"{param}={value} > max {param_schema['maximum']}")

    return result


def _check_type(value: any, expected_type: str, param_name: str) -> tuple[bool, str]:
    """Check if value matches expected JSON schema type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    expected_python_type = type_map.get(expected_type)
    if not expected_python_type:
        return True, ""  # Unknown type, skip

    if isinstance(value, expected_python_type):
        return True, ""

    return False, f"{param_name}: expected {expected_type}, got {type(value).__name__}"


def _fix_type_mismatches(args: dict, type_errors: dict, schema: dict) -> dict:
    """Attempt to fix type mismatches by converting values."""
    fixed_args = args.copy()

    for param, error_info in type_errors.items():
        expected_type = error_info["expected"]
        current_value = args[param]

        try:
            # Attempt type conversion
            if expected_type == "string":
                fixed_args[param] = str(current_value)
            elif expected_type == "integer":
                fixed_args[param] = int(current_value)
            elif expected_type == "number":
                fixed_args[param] = float(current_value)
            elif expected_type == "boolean":
                fixed_args[param] = bool(current_value)
            elif expected_type == "array":
                if not isinstance(current_value, list):
                    fixed_args[param] = [current_value]

            logger.info(f"  Fixed type: {param} {error_info['actual']}   {expected_type}")
        except Exception as e:
            logger.warning(f"    Could not fix type for '{param}': {e}")

    return fixed_args


def _extract_params_from_query(query: str, param_names: list[str], properties: dict) -> dict:
    """
    Extract parameter values from user query using simple heuristics.

    Args:
        query: User query text
        param_names: List of parameter names to extract
        properties: Parameter schema properties

    Returns:
        Dict of extracted param values
    """
    import re

    extracted = {}
    query_lower = query.lower()

    for param in param_names:
        param_type = properties.get(param, {}).get("type", "string")

        # Extract ticker symbols (most common case)
        if param in ("ticker", "symbol", "stock"):
            # Look for ticker patterns: BBCA.JK, AAPL, TSLA, etc.
            ticker_matches = re.findall(r"\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b", query.upper())
            if ticker_matches:
                extracted[param] = ticker_matches[0]
            # Or extract company name and try to convert
            elif "bank" in query_lower:
                # Common patterns: "BCA Bank"   BBCA.JK
                company_patterns = {
                    "bca bank": "BBCA.JK",
                    "mandiri": "BMRI.JK",
                    "bri": "BBRI.JK",
                    "tesla": "TSLA",
                    "apple": "AAPL",
                    "microsoft": "MSFT",
                }
                for company, ticker in company_patterns.items():
                    if company in query_lower:
                        extracted[param] = ticker
                        break

        # Extract query/search terms
        elif param in ("query", "search_query", "q"):
            # Use the entire query as search query
            extracted[param] = query[:200]  # Truncate to reasonable length

        # Extract period/timeframe
        elif param in ("period", "timeframe"):
            if "annual" in query_lower or "year" in query_lower:
                extracted[param] = "1y"
            elif "quarter" in query_lower:
                extracted[param] = "3mo"
            else:
                extracted[param] = "1y"  # Default to annual

        # Extract statement type for financial tools
        elif param in ("statement", "statement_type"):
            if "balance" in query_lower:
                extracted[param] = "balance_sheet"
            elif "income" in query_lower:
                extracted[param] = "income_statement"
            elif "cash" in query_lower:
                extracted[param] = "cash_flow"
            else:
                extracted[param] = "balance_sheet"  # Default

    return extracted


def _similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity score between two strings (0.0 - 1.0)."""
    from difflib import SequenceMatcher

    return SequenceMatcher(None, str1, str2).ratio()


# ============================================================================
# Tool Routing Logic
# ============================================================================

from kernel.actions.tool_loader import route_to_tool_dynamic


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
            # Simple extraction: look for ticker patterns, let retry loop fix errors
            ticker_match = re.search(r"\b([A-Z]{2,5}(?:\.[A-Z]{2,3})?)\b", query_upper)
            if ticker_match:
                variables[var] = ticker_match.group(1)
            else:
                # Fallback: use query company name, retry loop will correct via LLM
                variables[var] = query.strip()

        elif var.lower() == "company":
            # Use first few words as company name
            words = query.split()[:3]
            variables[var] = " ".join(words)

        elif var.lower() == "period":
            # Look for period patterns (1y, 6mo, 3mo, 1d, etc.)
            period_match = re.search(r"\b(\d+(?:y|mo|d|w))\b", query.lower())
            if period_match:
                variables[var] = period_match.group(1)
            else:
                variables[var] = "1y"  # Default

        elif var.lower() in ("source_url", "url"):
            # Look for URL patterns
            url_match = re.search(r"https?://[^\s]+", query)
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
        from kernel.interfaces.fact_store import get_fact_store
        from shared.hardware.detector import detect_hardware

        store = get_fact_store()
        hw = detect_hardware()
        fact_limit = hw.optimal_fact_limit()  # Hardware-aware limit

        if store:
            # Search for related past research with timeout to avoid blocking
            related_facts = await asyncio.wait_for(
                store.search(query, limit=fact_limit),
                timeout=5.0,  # 5 second timeout to avoid blocking research
            )

        if related_facts:
            logger.info(f"Planner: Found {len(related_facts)} related past facts")
            state["related_facts"] = [
                {"entity": f.entity, "value": f.value[:200], "source": f.source_url}
                for f in related_facts
            ]
    except TimeoutError:
        logger.warning("Planner: Related fact lookup timed out, skipping")
    except Exception as e:
        logger.debug(f"Related fact lookup skipped: {e}")

    # ============================================================
    # COMPLEXITY CLASSIFICATION (Dynamic Limit Scaling)
    # ============================================================
    try:
        from kernel.logic.complexity import classify_complexity

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

    # ============================================================
    # KNOWLEDGE CONTEXT RETRIEVAL (Domain Expertise from Knowledge Library)
    # ============================================================
    knowledge_context = ""
    try:
        from shared.knowledge.retriever import get_knowledge_retriever

        knowledge_retriever = get_knowledge_retriever()
        knowledge_context = await asyncio.wait_for(
            knowledge_retriever.retrieve_all(
                query=query,
                skill_limit=3,
                rule_limit=2,
            ),
            timeout=5.0,
        )
        if knowledge_context:
            logger.info(
                f"Planner: Retrieved {len(knowledge_context)} chars of domain knowledge   injecting into plan context"
            )
            state["knowledge_context"] = knowledge_context
        else:
            logger.info(
                "Planner: Knowledge retrieval returned empty   no domain expertise injected"
            )
    except TimeoutError:
        logger.warning("Planner: Knowledge retrieval timed out, skipping")
    except Exception as e:
        logger.warning(f"Planner: Knowledge retrieval failed: {e}")

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
                from kernel.templates.loader import get_template_loader

                loader = get_template_loader()

                matched_template = loader.match(query)
                if matched_template:
                    template = loader.load(matched_template)
                    if template:
                        logger.info(f"  Using template: {matched_template}")

                        # Extract variables from query
                        variables = _extract_template_variables(
                            query, template.get("variables", [])
                        )

                        # Expand template into tasks
                        expanded_tasks = loader.expand(template, variables)

                        # Generate execution plan from expanded template
                        execution_plan = generate_execution_plan_from_blueprint(
                            query, {"blueprint": expanded_tasks}
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
                from kernel.interfaces.tool_registry import get_tool_registry

                registry = get_tool_registry()

                # 1. Try High-Limit Semantic Search (RAG)
                # This scales to 10k+ tools by finding only relevant ones
                relevant_tools = []
                if registry:
                    try:
                        # Search specifically for tools that match the query intention
                        search_results = await asyncio.wait_for(
                            registry.search_tools(
                                query, limit=50
                            ),  # Reduced limit for schema inclusion
                            timeout=5.0,
                        )

                        if search_results:
                            logger.info(f"Planner: RAG found {len(search_results)} relevant tools")
                            # Format: "tool_name: {input_schema}" for precise mapping
                            for t in search_results:
                                name = t.get("name", "N/A")
                                # Optimized for Front-Loaded Docstrings: Summary (200 chars) + context (200 chars)
                                desc = t.get("description", "")[:400]
                                schema = t.get("inputSchema", {})

                                # Format schema as JSON for LLM clarity (not Python dict)
                                import json

                                schema_json = json.dumps(schema, indent=2)
                                # Escape braces for f-string
                                schema_escaped = schema_json.replace("{", "{{").replace("}", "}}")

                                # Extract required parameters for emphasis
                                required_params = schema.get("required", [])
                                properties = schema.get("properties", {})

                                tool_doc = f"TOOL: {name}\n"
                                tool_doc += f"DESCRIPTION: {desc}\n"
                                if required_params:
                                    tool_doc += f"REQUIRED PARAMS: {', '.join(required_params)}\n"
                                tool_doc += f"FULL SCHEMA (JSON):\n{schema_escaped}\n"

                                relevant_tools.append(tool_doc)
                    except Exception as search_err:
                        logger.warning(
                            f"Planner RAG Search failed: {search_err}. Falling back to active list."
                        )

                # 2. Fallback: List Active/Cached Tools (Safety Net)
                if not relevant_tools:
                    if registry.tool_to_server:
                        known_tools = list(registry.tool_to_server.keys())
                        # Slice to avoid context overflow
                        target_tools = known_tools[:50]  # Reduced from 100 to fit context
                        logger.warning(
                            f"Planner: RAG search failed, using fallback list of {len(target_tools)} tools (NAME ONLY - schemas unavailable)"
                        )

                        # Fallback: Tool names only (no schemas available without RAG)
                        # This will cause the LLM to make best-effort parameter guessing
                        # which is why we have the retry loop in unified_tool_handler
                        relevant_tools = [
                            f"TOOL: {t}\nDESCRIPTION: (schema unavailable - use retry loop for parameter correction)\n"
                            for t in target_tools
                        ]
                    else:
                        # 3. Last Resort: Try to force discovery once
                        try:
                            logger.info("Planner: Registry empty, forcing tool scan...")
                            all_tools = await asyncio.wait_for(
                                registry.list_all_tools(), timeout=5.0
                            )
                            # Here we HAVE schemas
                            import json

                            for t in all_tools[:50]:
                                name = t.get("name", "N/A")
                                # Optimized for Front-Loaded Docstrings
                                desc = t.get("description", "")[:400]
                                schema = t.get("inputSchema", {})

                                # Format schema as JSON (not Python dict)
                                schema_json = json.dumps(schema, indent=2)
                                schema_escaped = schema_json.replace("{", "{{").replace("}", "}}")

                                # Extract required parameters
                                required_params = schema.get("required", [])

                                tool_doc = f"TOOL: {name}\n"
                                tool_doc += f"DESCRIPTION: {desc}\n"
                                if required_params:
                                    tool_doc += f"REQUIRED PARAMS: {', '.join(required_params)}\n"
                                tool_doc += f"FULL SCHEMA (JSON):\n{schema_escaped}\n"

                                relevant_tools.append(tool_doc)
                        except TimeoutError:
                            pass

                # Format for LLM
                if relevant_tools:
                    tools_context = f"RELEVANT TOOLS ({len(relevant_tools)} found):\n"
                    tools_context += "\n".join(relevant_tools)
                else:
                    tools_context = (
                        "No specific tools found. Rely on 'web_search' and 'execute_code'."
                    )

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
  Generate as many steps as the query ACTUALLY requires   do NOT default to 3."""

            # ============================================================
            # ERROR FEEDBACK LOOP (Self-Correction from Previous Failures)
            # Inject previous tool failures so LLM learns from mistakes
            # ============================================================
            error_feedback_section = ""
            error_feedback = state.get("error_feedback", [])
            if error_feedback:
                error_feedback_section = "\n\n    PREVIOUS TOOL FAILURES (LEARN FROM THESE):\n"
                error_feedback_section += (
                    "The following tool calls FAILED in the previous iteration. "
                )
                error_feedback_section += "You MUST correct these mistakes:\n\n"
                for i, err in enumerate(
                    error_feedback[:5], 1
                ):  # Limit to 5 to avoid context overflow
                    error_feedback_section += f"{i}. TOOL: {err.get('tool', 'unknown')}\n"
                    error_feedback_section += f"   FAILED ARGS: {err.get('args', {})}\n"
                    error_feedback_section += f"   ERROR: {err.get('error', 'unknown')[:200]}\n"
                    error_feedback_section += f"   TASK: {err.get('description', '')[:100]}\n"
                    # Include dynamic suggestion if present
                    if err.get("suggestion"):
                        error_feedback_section += f"     SUGGESTION: {err.get('suggestion')}\n"
                    error_feedback_section += "\n"
                error_feedback_section += "CORRECTION GUIDANCE:\n"
                error_feedback_section += "- If ticker was wrong, use search_ticker('company name') to find the correct symbol FIRST\n"
                error_feedback_section += "- If parameter was missing, ensure you include ALL required parameters from the schema\n"
                error_feedback_section += (
                    "- If tool doesn't exist, use an alternative from the AVAILABLE TOOLS list\n"
                )

            # Build knowledge section for prompt
            knowledge_section = ""
            if knowledge_context:
                knowledge_section = f"""

{knowledge_context}

Use the above domain expertise to inform your planning decisions,
tool selection, and parameter choices. Follow the reasoning frameworks
and output standards defined in the retrieved knowledge."""

            # JSON Blueprint System Prompt (Level 30 Architect)
            from shared.prompts import get_agent_prompt

            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=get_agent_prompt("planner").format(
                        complexity_guidance=complexity_guidance,
                        error_feedback_section=error_feedback_section,
                        knowledge_section=knowledge_section,
                        tools_context=tools_context,
                    ),
                ),
                LLMMessage(role=LLMRole.USER, content=query),
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
                json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", content)
                if json_match:
                    content = json_match.group(1)
                # Or find raw JSON object
                elif content.startswith("{"):
                    pass  # Already JSON
                else:
                    # Try to find JSON anywhere in response
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        content = content[json_start:json_end]

                blueprint = json.loads(content)
                logger.info(
                    f"Planner: Parsed JSON Blueprint with {len(blueprint.get('blueprint', []))} steps"
                )

            except json.JSONDecodeError as e:
                logger.warning(f"Planner: JSON parse failed ({e}), falling back to text parsing")
                blueprint = None

            if blueprint and "blueprint" in blueprint:
                # Generate execution plan from JSON Blueprint
                execution_plan = generate_execution_plan_from_blueprint(query, blueprint)

                # CRITICAL: Validate and correct tool names against 2K+ tool registry
                try:
                    execution_plan = await _validate_and_correct_tool_names(execution_plan)
                except Exception as val_err:
                    logger.warning(
                        f"Tool validation failed: {val_err}, proceeding with unvalidated tools"
                    )

                # CRITICAL: Validate arguments are not empty for required parameters
                try:
                    execution_plan = await _validate_tool_arguments(execution_plan, query)
                except Exception as arg_err:
                    logger.warning(f"Argument validation failed: {arg_err}")

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
                    elif line.startswith(("-", "*", " ")):
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
            state["execution_plan"] = generate_execution_plan_phased(
                query, {"research": [query]}
            ).model_dump()
            logger.info("Planner: No LLM, using query as-is")

    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["sub_queries"] = [query]
        state["hypotheses"] = []
        state["execution_plan"] = generate_execution_plan_phased(
            query, {"research": [query]}
        ).model_dump()

    state["status"] = "planning_complete"
    return state


def generate_execution_plan_phased(
    query: str, execution_phases: dict[str, list[str]]
) -> ExecutionPlan:
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
            previous_phase = phase_names[i - 1]
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
                depends_on=depends_on,  # STRICT DEPENDENCY
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
            "condition",
            "true_branch",
            "false_branch",
            "true",
            "false",
            "loop_over",
            "over",
            "loop_body",
            "body",
            "loop_variable",
            "merge_inputs",
            "merge_strategy",
            "goal",
            "agent_max_steps",
            "agent_tools",
            "max_steps",
            "tools",
            "llm_prompt",
            "llm_system",
            "prompt",
            "system",
            "max_parallel",
        ):
            if adv_key in step:
                node_config[adv_key] = step[adv_key]

        micro_task = MicroTask(
            task_id=step_id,
            description=step.get(
                "description",
                f"{tool_name}: {args.get('query', args.get('code', str(args)[:100]))}",
            ),
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
