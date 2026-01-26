
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import os
import json

logger = get_logger(__name__)

def dict_to_result(data: dict) -> ToolResult:
    return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])

async def tokenize_formula(arguments: dict) -> ToolResult:
    """Parse a formula string into tokens."""
    try:
        formula = arguments['formula']
        
        tok = Tokenizer(formula)
        tokens = []
        for t in tok.items:
            tokens.append({
                "value": t.value,
                "type": t.type,
                "subtype": t.subtype
            })
            
        return dict_to_result({"tokens": tokens, "count": len(tokens)})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_formula_references(arguments: dict) -> ToolResult:
    """Extract cell references from a formula."""
    try:
        formula = arguments['formula']
        tok = Tokenizer(formula)
        refs = []
        for t in tok.items:
            if t.type == "OPERAND" and t.subtype == "RANGE":
                refs.append(t.value)
        
        return dict_to_result({"references": list(set(refs))})
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
