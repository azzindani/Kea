
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import dict_to_result
import os
import re

# Minimal Loughran-McDonald Sentiment Word Lists (Representative subset for lightweight implementation)
NEGATIVE_WORDS = {
    "loss", "losses", "fail", "failure", "failed", "risk", "risks", "uncertainty", "uncertain",
    "adverse", "adversely", "against", "litigation", "claim", "claims", "impairment", "write-down",
    "restatement", "misstatement", "correction", "volatile", "volatility", "decline", "declined",
    "decrease", "decreased", "default", "bankruptcy", "insolvency", "negative", "negatively",
    "challenging", "difficulty", "difficulties", "shortfall", "shortage", "suspend", "suspended"
}

POSITIVE_WORDS = {
    "gain", "gains", "profit", "profits", "positive", "positively", "success", "successful", "successfully",
    "growth", "grow", "grown", "improve", "improvement", "improved", "benefit", "beneficial", "benefited",
    "opportunity", "opportunities", "strength", "strengthen", "strong", "excellent", "exceptional",
    "effective", "effectively", "efficient", "efficiency", "innovate", "innovation", "innovative",
    "record", "achieve", "achievement", "achieved", "exceed", "exceeded", "surpass", "surpassed"
}

async def extract_filing_section(arguments: dict) -> ToolResult:
    """
    Extract a specific section from a 10-K or 10-Q (e.g., 'Item 1A. Risk Factors').
    Heuristic extraction based on Item headers.
    Args:
        path: File path.
        item: "1A", "7" (MD&A), "7A", "8".
    """
    try:
        path = arguments['path']
        item = arguments['item'].upper().replace("ITEM ", "")
        
        if not os.path.exists(path): return ToolResult(isError=True, content=[TextContent(text="File not found.")])
        with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
            
        # Regex to find Item Headers
        # They often look like: "Item 7. Management's Discussion..."
        # Or bolded with HTML tags.
        # We look for the start and the likely next item.
        
        # Map Item to Next Item (heuristic)
        next_map = {
            "1": ["1A", "1B", "2"],
            "1A": ["1B", "2"],
            "7": ["7A", "8"], # MD&A -> Quant Risk -> Financials
            "7A": ["8"],
            "8": ["9"]
        }
        
        # normalization
        normalized_content = re.sub(r'<[^>]+>', ' ', content) # Strip HTML tags roughly
        normalized_content = re.sub(r'\s+', ' ', normalized_content) # Collapse whitespace
        
        # Regex construction: "Item X." ... "Item Y."
        # Case insensitive, allow localized formatting
        
        start_pattern = rf"Item\s+{re.escape(item)}[\.\:\s]"
        
        # Find all start indices
        starts = [m.start() for m in re.finditer(start_pattern, normalized_content, re.IGNORECASE)]
        
        if not starts:
             return dict_to_result({"found": False, "item": item}, "Section Not Found")
             
        # Often the first match is the Table of Contents. We usually want the LAST match or the longest block.
        # But in 10-K, ToC is small. Real list is later.
        # Let's try to find End pattern after the LAST start match that has substantial content?
        # Or try to extract from the *second* match if multiple exist?
        
        # Let's try to extract multiple candidates and return longest
        candidates = []
        possible_ends = next_map.get(item, [])
        
        end_pattern = "|".join([rf"Item\s+{re.escape(nx)}[\.\:\s]" for nx in possible_ends])
        
        for s_idx in starts:
            # Look for end after s_idx
            if end_pattern:
                end_match = re.search(end_pattern, normalized_content[s_idx+20:], re.IGNORECASE) # +20 buffer
                if end_match:
                    e_idx = s_idx + 20 + end_match.start()
                    text = normalized_content[s_idx:e_idx]
                    candidates.append(text)
                else:
                    # No end found, take chunk
                    candidates.append(normalized_content[s_idx:s_idx+50000])
        
        # Sort by length descending, pick longest (usually the actual section, not ToC)
        if candidates:
            candidates.sort(key=len, reverse=True)
            best_text = candidates[0]
            # Trim
            best_text = best_text[:100000] # Cap size
            return dict_to_result({
                "found": True, 
                "item": item, 
                "text_length": len(best_text), 
                "text_preview": best_text[:500],
                "full_text_marker": "available in 'text' field (truncated in preview)"
            }, "Extracted Section")
            
        return dict_to_result({"found": False}, "Extraction Failed")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def calculate_filing_sentiment(arguments: dict) -> ToolResult:
    """
    Analyze sentiment of a filing (or text).
    """
    try:
        text = arguments.get('text')
        path = arguments.get('path')
        
        if path and not text:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
        
        if not text: return ToolResult(isError=True, content=[TextContent(text="No text provided.")])
        
        # Tokenize roughly
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        total = len(words)
        
        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
        
        polarity = (pos_count - neg_count) / (pos_count + neg_count + 1)
        subjectivity = (pos_count + neg_count) / (total + 1)
        
        return dict_to_result({
            "total_words": total,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "polarity_score": polarity, # -1 to 1
            "subjectivity_score": subjectivity,
            "note": "Based on specialized financial sentiment dictionary (subset)."
        }, "Sentiment Analysis")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
