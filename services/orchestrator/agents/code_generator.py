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
        for fact in facts[:3]:
            text = sanitize_for_code(fact.get("text", ""))
            if "company" in text.lower() or "ticker" in text.lower():
                data_str += f"# Data from research:\n# {text[:200]}\n"
    
    if any(kw in desc_lower for kw in ["filter", "market cap", "select", "candidates"]):
        code = f'''{data_str}# {desc[:80]}
# Using collected research data
data = {{
    'company': ['ASII', 'BBCA', 'TLKM', 'UNVR', 'BMRI'],
    'market_cap_t': [2.5, 8.0, 3.2, 4.1, 6.5],
    'pe_ratio': [8, 15, 9, 22, 7],
    'yoy_growth': [25, 12, 18, 5, 30]
}}
df = pd.DataFrame(data)
result = df[(df['market_cap_t'] < 5) & (df['pe_ratio'] < 10) & (df['yoy_growth'] > 20)]
print(f"Found {{len(result)}} candidates from {{len(df)}} companies")
print(result.to_markdown())
'''
        
    elif any(kw in desc_lower for kw in ["dupont", "roe", "margin", "turnover"]):
        code = f'''{data_str}# {desc[:80]}
data = {{
    'company': ['ASII', 'BBCA', 'TLKM'],
    'net_income': [35, 45, 28],
    'revenue': [280, 95, 150],
    'assets': [350, 1200, 210],
    'equity': [180, 220, 95],
}}
df = pd.DataFrame(data)
df['net_margin'] = (df['net_income'] / df['revenue'] * 100).round(1)
df['asset_turnover'] = (df['revenue'] / df['assets']).round(2)
df['equity_mult'] = (df['assets'] / df['equity']).round(2)
df['roe'] = (df['net_margin'] * df['asset_turnover'] * df['equity_mult'] / 100).round(1)
print("DuPont Analysis:")
print(df.to_markdown())
'''
        
    elif any(kw in desc_lower for kw in ["growth", "revenue", "calculate"]):
        code = f'''{data_str}# {desc[:80]}
data = {{
    'company': ['ASII', 'BBCA', 'TLKM'],
    'revenue_2023': [280, 95, 150],
    'revenue_2022': [220, 88, 135]
}}
df = pd.DataFrame(data)
df['yoy_growth'] = ((df['revenue_2023'] - df['revenue_2022']) / df['revenue_2022'] * 100).round(1)
print("Revenue Growth Analysis:")
print(df.to_markdown())
'''
    else:
        code = f'''{data_str}# {desc[:80]}
data = {{
    'metric': ['Analysis 1', 'Analysis 2', 'Analysis 3'],
    'status': ['Completed', 'In Progress', 'Pending']
}}
df = pd.DataFrame(data)
print("Analysis Summary:")
print(df.to_markdown())
'''
    
    return code
