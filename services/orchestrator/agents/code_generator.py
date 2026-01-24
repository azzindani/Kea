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
from shared.logging import get_logger

logger = get_logger(__name__)


def sanitize_for_code(text: str) -> str:
    """
    Sanitize text for embedding in Python code.
    Removes non-ASCII characters that cause SyntaxError.
    """
    # Normalize Unicode (convert special chars to ASCII equivalents)
    text = unicodedata.normalize('NFKD', text)
    # Remove non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Code generation prompt - instructs LLM to write executable Python
CODE_PROMPT = """You are a Python code generator for financial analysis.

TASK: {task_description}

COLLECTED FACTS (from prior research):
{facts_summary}

AVAILABLE IN SANDBOX:
- pd (pandas)
- np (numpy)  
- duckdb
- Standard builtins (print, len, sum, etc.)

RULES:
1. DO NOT use import statements (pd, np, duckdb already loaded)
2. Generate ONLY executable Python code
3. Use the ACTUAL data from the facts above
4. Print results in markdown table format
5. Keep code under 30 lines

Generate Python code:
```python
"""


async def generate_python_code(
    task_description: str,
    facts: list[dict],
    context_summary: str = "",
) -> str:
    """
    Use LLM to generate Python code based on task and collected facts.
    
    Args:
        task_description: What the code should accomplish
        facts: List of fact dicts from prior research tasks
        context_summary: Summary of available context
        
    Returns:
        Executable Python code string (no imports)
    """
    # Check if we have API key
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.warning("No OPENROUTER_API_KEY, using fallback code generator")
        return generate_fallback_code(task_description, facts)
    
    try:
        from shared.llm.openrouter import OpenRouterProvider
        from shared.llm.provider import LLMMessage, LLMConfig, MessageRole
        
        # Summarize facts for LLM
        facts_summary = ""
        for i, fact in enumerate(facts[:10], 1):  # Use up to 10 facts
            text = fact.get("text", "")[:500]
            source = fact.get("source", "unknown")
            facts_summary += f"\n[Fact {i}] (from {source}):\n{text}\n"
        
        if not facts_summary:
            facts_summary = "(No facts collected yet - use sample data)"
        
        prompt = CODE_PROMPT.format(
            task_description=task_description,
            facts_summary=facts_summary,
        )
        
        provider = OpenRouterProvider(api_key=api_key)
        response = await provider.complete(
            messages=[LLMMessage(role=MessageRole.USER, content=prompt)],
            config=LLMConfig(
                temperature=0.2,  # Low temp for deterministic code
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
        lines = code.strip().split('\n')
        lines = [l for l in lines if not l.strip().startswith('import ')]
        code = '\n'.join(lines)
        
        logger.info(f"   📝 LLM generated code ({len(code)} chars)")
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
    code = f'''{data_str}# Task: {desc[:80]}
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
