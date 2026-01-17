"""
LLM Code Generator - Generates executable Python code from task descriptions.

This module uses the LLM to generate actual executable Python code
instead of placeholder text, enabling real data analysis.
"""

from __future__ import annotations

from shared.logging import get_logger

logger = get_logger(__name__)


CODE_GENERATION_PROMPT = """You are a Python code generator for financial data analysis.

TASK: {task_description}

AVAILABLE CONTEXT:
{context_summary}

REQUIREMENTS:
1. Generate ONLY executable Python code
2. Use pandas for data operations
3. Include proper imports
4. Print results at the end
5. Handle missing data gracefully
6. Keep code concise (< 50 lines)

AVAILABLE DATA:
{available_data}

Generate Python code that completes this task:
```python
"""

SIMPLE_CODE_TEMPLATES = {
    "filter": '''import pandas as pd

# {task_description}
# Create sample data if not available
data = {sample_data}
df = pd.DataFrame(data)

# Apply filter
result = df[{filter_condition}]
print(f"Filtered to {{len(result)}} rows")
print(result.head(10).to_markdown())
''',
    
    "calculate": '''import pandas as pd
import numpy as np

# {task_description}
data = {sample_data}
df = pd.DataFrame(data)

# Calculation
{calculation_code}

print("Results:")
print(result if 'result' in dir() else df.head(10).to_markdown())
''',
    
    "analyze": '''import pandas as pd
import numpy as np

# {task_description}
data = {sample_data}
df = pd.DataFrame(data)

# Analysis
summary = df.describe()
print("Data Summary:")
print(summary.to_markdown())
''',
}


async def generate_python_code(
    task_description: str,
    context_summary: str = "",
    available_data: dict | None = None,
) -> str:
    """
    Generate executable Python code using LLM.
    
    Args:
        task_description: What the code should do
        context_summary: Summary of available context
        available_data: Dict of data available (keys and types)
        
    Returns:
        Executable Python code string
    """
    try:
        llm = get_llm_provider()
        
        prompt = CODE_GENERATION_PROMPT.format(
            task_description=task_description,
            context_summary=context_summary or "No prior context",
            available_data=str(available_data) if available_data else "No data stored yet",
        )
        
        response = await llm.complete(
            prompt=prompt,
            temperature=0.2,  # Lower temp for code
            max_tokens=500,
        )
        
        # Extract code from response
        code = response.strip()
        
        # Remove markdown code blocks if present
        if "```python" in code:
            code = code.split("```python")[1]
            if "```" in code:
                code = code.split("```")[0]
        elif "```" in code:
            code = code.split("```")[1]
            if "```" in code:
                code = code.split("```")[0]
        
        # Ensure basic imports
        if "import pandas" not in code and "pd." in code:
            code = "import pandas as pd\n" + code
        
        logger.info(f"   📝 Generated Python code ({len(code)} chars)")
        return code.strip()
        
    except Exception as e:
        logger.warning(f"Code generation failed: {e}, using fallback")
        return generate_fallback_code(task_description)


def generate_fallback_code(task_description: str) -> str:
    """
    Generate simple fallback code based on task type.
    
    Args:
        task_description: Task description
        
    Returns:
        Simple Python code
    """
    desc_lower = task_description.lower()
    
    # Detect task type from description
    if any(kw in desc_lower for kw in ["filter", "retain", "keep", "select"]):
        template = "filter"
        sample = "{'company': ['A', 'B', 'C'], 'market_cap': [1e12, 6e12, 3e12], 'pe_ratio': [8, 12, 7]}"
        condition = "(df['market_cap'] < 5e12) & (df['pe_ratio'] < 10)"
        
        code = f'''import pandas as pd

# {task_description[:100]}
data = {sample}
df = pd.DataFrame(data)

# Apply filter
result = df[{condition}]
print(f"Filtered to {{len(result)}} rows")
print(result.to_markdown())
'''
        
    elif any(kw in desc_lower for kw in ["calculate", "compute", "ratio", "growth"]):
        code = f'''import pandas as pd
import numpy as np

# {task_description[:100]}
data = {{'company': ['A', 'B', 'C'], 'revenue_2023': [100, 200, 150], 'revenue_2022': [80, 160, 140]}}
df = pd.DataFrame(data)

# Calculate YoY growth
df['yoy_growth'] = (df['revenue_2023'] - df['revenue_2022']) / df['revenue_2022'] * 100
print("Revenue Growth Analysis:")
print(df.to_markdown())
'''
        
    elif any(kw in desc_lower for kw in ["dupont", "roe", "margin", "turnover"]):
        code = f'''import pandas as pd

# {task_description[:100]}
# DuPont Analysis: ROE = Net Margin × Asset Turnover × Equity Multiplier
data = {{
    'company': ['A', 'B', 'C'],
    'net_income': [10, 20, 15],
    'revenue': [100, 150, 120],
    'assets': [200, 300, 250],
    'equity': [80, 120, 100],
}}
df = pd.DataFrame(data)

df['net_margin'] = df['net_income'] / df['revenue']
df['asset_turnover'] = df['revenue'] / df['assets']
df['equity_multiplier'] = df['assets'] / df['equity']
df['roe'] = df['net_margin'] * df['asset_turnover'] * df['equity_multiplier']

print("DuPont Analysis:")
print(df[['company', 'net_margin', 'asset_turnover', 'equity_multiplier', 'roe']].to_markdown())
'''
        
    else:
        # Generic analysis code
        code = f'''import pandas as pd

# {task_description[:100]}
data = {{'item': ['Analysis 1', 'Analysis 2'], 'result': ['Pending data', 'Pending data']}}
df = pd.DataFrame(data)
print("Analysis placeholder - real data needed:")
print(df.to_markdown())
'''
    
    return code


def extract_code_from_response(response: str) -> str:
    """Extract Python code from LLM response."""
    # Try to find code block
    if "```python" in response:
        parts = response.split("```python")
        if len(parts) > 1:
            code = parts[1].split("```")[0]
            return code.strip()
    
    if "```" in response:
        parts = response.split("```")
        if len(parts) > 1:
            return parts[1].strip()
    
    # Return as-is if no code blocks
    return response.strip()
