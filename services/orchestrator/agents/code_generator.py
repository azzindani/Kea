"""
LLM Code Generator - LLM generates Python code based on research context.

The LLM autonomously writes Python code based on:
1. The task description
2. Facts collected from prior tasks
3. Data available in context pool

This enables true autonomous data processing - Kea decides what code to write.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from shared.logging import get_logger
from shared.prompts import get_code_prompt

logger = get_logger(__name__)


# Pattern for {{step_id.artifact}} or {{step_id.artifacts.key}} placeholders
PLACEHOLDER_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


def sanitize_for_code(text: str) -> str:
    """
    Sanitize text for embedding in Python code.
    Removes non-ASCII characters that cause SyntaxError.
    """
    # Normalize Unicode (convert special chars to ASCII equivalents)
    text = unicodedata.normalize("NFKD", text)
    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    # Clean up multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def resolve_placeholders(text: str, context_data: dict[str, Any] | None = None) -> str:
    """
    Resolve {{placeholder}} syntax with actual values from context.

    Handles formats like:
        - {{s1.artifact}} -> Looks up task 's1' file in context_pool
        - {{step_1.artifacts.prices_csv}} -> Looks up nested path
        - {{fetch_data.artifact}} -> Converts to actual file path

    Args:
        text: String potentially containing placeholders
        context_data: Dict mapping step_id/keys to actual values

    Returns:
        String with placeholders replaced by actual values
    """
    # Build comprehensive context from context_pool
    try:
        from shared.context_pool import get_context_pool

        ctx = get_context_pool()

        # Build lookup dict from context_pool
        context_data = context_data or {}

        # Add all stored files (task_id -> path)
        for key in ctx.list_data_keys():
            data = ctx.get_data(key)
            context_data[key] = data

        # Add file artifacts
        for path in ctx.list_files():
            # Extract task_id from path if possible (e.g., "/vault/s1_income.csv" -> "s1")
            import os

            basename = os.path.basename(path)
            # Try patterns like "s1_...", "task_1_..."
            if "_" in basename:
                prefix = basename.split("_")[0]
                if prefix not in context_data:
                    context_data[prefix] = path

        # Add explicit file lookups
        if hasattr(ctx, "_file_store"):
            for task_id, info in ctx._file_store.items():
                if isinstance(info, dict):
                    context_data[task_id] = info.get("path", str(info))
                else:
                    context_data[task_id] = str(info)

        # Add code results
        if hasattr(ctx, "_code_results"):
            for task_id, result in ctx._code_results.items():
                context_data[f"{task_id}_result"] = result

    except Exception as e:
        logger.debug(f"Could not load context_pool: {e}")
        context_data = context_data or {}

    if not context_data:
        return text

    def replace_placeholder(match: re.Match) -> str:
        path = match.group(1)
        parts = path.split(".")
        task_id = parts[0]  # e.g., "s1" from "s1.artifact"

        # Strategy 1: Direct task_id lookup in context
        if task_id in context_data:
            value = context_data[task_id]
            # Navigate nested path if present (skip artifact/artifacts keywords)
            for part in parts[1:]:
                if part in ("artifact", "artifacts"):
                    continue  # Skip these markers
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
            return repr(str(value))  # Quoted string for Python

        # Strategy 2: Try context_pool.get_file() directly
        try:
            from shared.context_pool import get_context_pool

            ctx = get_context_pool()
            file_path = ctx.get_file(task_id)
            if file_path:
                logger.info(f"   ✅ Resolved {{{{task_id}}}} -> {file_path}")
                return repr(str(file_path))

            # Try get_data for non-file artifacts
            data = ctx.get_data(task_id)
            if data is not None:
                return repr(str(data))
        except Exception:
            pass

        # Strategy 3: Full path lookup (e.g., "step_1.artifacts.prices_csv")
        full_key = path.replace(".artifacts.", ".").replace(".artifact", "")
        if full_key in context_data:
            return repr(str(context_data[full_key]))

        # Strategy 4: Look for task_output_* keys
        task_output_key = f"task_output_{task_id}"
        if task_output_key in context_data:
            return repr(str(context_data[task_output_key]))

        # Return empty string for unresolved (safer than crashing)
        logger.warning(f"⚠️ Could not resolve placeholder: {path}")
        return "''"  # Empty string to prevent syntax errors

    return PLACEHOLDER_PATTERN.sub(replace_placeholder, text)


async def generate_python_code(
    task_description: str,
    facts: list[dict],
    file_artifacts: list[str] | None = None,
    previous_code: str | None = None,
    previous_error: str | None = None,
    context_data: dict[str, Any] | None = None,
) -> str:
    """
    Use LLM to generate Python code based on task and collected facts.
    Supports self-correction if previous attempt failed.

    Args:
        task_description: What the code should accomplish
        facts: List of fact dicts from prior research tasks
        file_artifacts: List of available file paths
        previous_code: The code that failed (for retry)
        previous_error: The error message (for retry)
        context_data: Dict mapping step_ids to their output values (for resolving {{placeholders}})

    Returns:
        Executable Python code string (no imports)
    """
    # Build context_data from context pool if not provided
    if context_data is None:
        try:
            from shared.context_pool import get_context_pool

            ctx = get_context_pool()
            context_data = ctx.get_all_data() if hasattr(ctx, "get_all_data") else {}

            # Also add stored artifacts
            if hasattr(ctx, "_data_store"):
                context_data.update(ctx._data_store)
        except Exception:
            context_data = {}

    # Check if we have API key
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.warning("No OPENROUTER_API_KEY, using fallback code generator")
        return generate_fallback_code(task_description, facts)

    try:
        from shared.config import get_settings
        from shared.llm.openrouter import OpenRouterProvider
        from shared.llm.provider import LLMConfig, LLMMessage, LLMRole

        # Summarize facts for LLM
        facts_summary = ""
        for i, fact in enumerate(facts[:15], 1):  # Use up to 15 facts
            text = fact.get("text", "")[:500]
            source = fact.get("source", "unknown")
            facts_summary += f"\n[Fact {i}] (from {source}):\n{text}\n"

        if not facts_summary:
            facts_summary = (
                "(No facts collected yet - if task requires data, assume it needs to be fetched)"
            )

        # Summarize files
        files_str = (
            "\n".join(f"- {f}" for f in (file_artifacts or []))
            if file_artifacts
            else "(No files available)"
        )

        # Build resolved data summary (showing what placeholders would resolve to)
        resolved_data_str = ""
        if context_data:
            for key, value in list(context_data.items())[:10]:  # Limit to 10 entries
                if isinstance(value, str) and len(value) > 200:
                    resolved_data_str += f"- {key}: (data with {len(value)} chars)\n"
                else:
                    resolved_data_str += f"- {key}: {repr(str(value)[:100])}\n"
        if not resolved_data_str:
            resolved_data_str = "(No pre-resolved data available)"

        # Resolve any placeholders in the task description
        resolved_task = resolve_placeholders(task_description, context_data)

        # Build prompt
        prompt = get_code_prompt().format(
            task_description=resolved_task,
            facts_summary=facts_summary,
            file_artifacts=files_str,
            resolved_data=resolved_data_str,
        )

        # Add Error Context (Self-Correction)
        if previous_error:
            prompt += f"""
\n\n!!! PREVIOUS ATTEMPT FAILED !!!
CODE:
```python
{previous_code or "Unknown"}
```

ERROR:
{previous_error}

INSTRUCTION: Fix the code above to resolve the error. Ensure you handle the edge case described in the error.
"""

        settings = get_settings()
        provider = OpenRouterProvider(api_key=api_key)
        response = await provider.complete(
            messages=[LLMMessage(role=LLMRole.USER, content=prompt)],
            config=LLMConfig(
                model=settings.models.generator_model,
                temperature=0.1,  # Lower temp for fixes
                max_tokens=32768,
            ),
        )

        code = response.content.strip()

        # Extract code from markdown block if present
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]

        # Remove any import statements (sandbox has pd/np pre-loaded)
        lines = code.strip().split("\n")
        lines = [l for l in lines if not l.strip().startswith("import ")]
        code = "\n".join(lines)

        # CRITICAL: Resolve any {{placeholder}} syntax in the generated code
        # The LLM may generate code like: pd.read_csv('{{s1.artifact}}')
        # We need to replace these with actual file paths from context_data
        if context_data and PLACEHOLDER_PATTERN.search(code):
            logger.info("   🔧 Resolving placeholders in generated code...")
            code = resolve_placeholders(code, context_data)

        logger.info(
            f"   📝 GENERATED PYTHON CODE (Self-Correction={bool(previous_error)}):\n{'-' * 60}\n{code}\n{'-' * 60}"
        )
        return code.strip()

    except Exception as e:
        logger.warning(f"LLM code generation failed: {e}, using fallback")
        return generate_fallback_code(task_description, facts)


def generate_fallback_code(task_description: str, facts: list[dict] | None = None) -> str:
    """
    Generate fallback code when LLM is unavailable.
    Uses facts from prior tasks if available.

    NOTE: pd, np, duckdb are pre-loaded in sandbox - NO imports needed.
    """
    # Sanitize description to remove Unicode chars that break Python
    desc = sanitize_for_code(task_description)
    desc_lower = desc.lower()

    # Extract any data from facts if available (sanitized)
    data_str = ""
    if facts:
        for fact in facts[:5]:
            text = sanitize_for_code(fact.get("text", ""))
            # Comment out facts to verify execution without relying on them blindly
            data_str += f"# Context: {text[:200]}\n"

    # Generic wrapper for data processing
    code = rf'''{data_str}# Task: {desc[:80]}
# WARNING: Live Logic Required.
# This fallback code suggests ensuring data is available.

import pandas as pd

# Check if we have data inputs
print("Analyzing request: {desc[:50]}...")

try:
    import yfinance as yf
    print("Environment has yfinance. Attempting to fetch relevant data if needed.")
    
    # Simple heuristic to fetch data if tickers are mentioned in description
    import re
    tickers = re.findall(r'[A-Z]{{4}}(?:\.[A-Z]{{2}})?', "{desc}")
    
    if tickers:
        print(f"Detected tickers: {{tickers}}")
        data = []
        for t in tickers:
            try:
                # Add exchange suffix if missing for generic context (assuming JK for Indonesian context of query)
                if "." not in t and len(t) == 4:
                    full_t = t + ".JK"
                else:
                    full_t = t
                    
                stock = yf.Ticker(full_t)
                info = stock.info
                if info and 'marketCap' in info:
                    data.append({{
                        "symbol": full_t,
                        "market_cap": info.get("marketCap", 0),
                        "pe_ratio": info.get("trailingPE", 0),
                        "revenue": info.get("totalRevenue", 0),
                        "name": info.get("longName", "Unknown")
                    }})
            except Exception:
                pass
                
        if data:
            df = pd.DataFrame(data)
            print("Fetched Live Data:")
            print(df.to_markdown())
        else:
            print("Could not fetch live data for detected tickers.")
    else:
        print("No tickers detected in task description for auto-fetch.")

except ImportError:
    print("yfinance not available in this sandbox. Please use 'finance_server' tools to collect data first.")

print("\\nNOTE: To prevent hallucinations, specific data retrieval tools should be used.")
'''
    return code
