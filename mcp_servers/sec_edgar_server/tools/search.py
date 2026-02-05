
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import os
import re
import glob

async def search_filing_content(arguments: dict) -> ToolResult:
    """
    Search for a keyword/regex within a single filing.
    """
    path = arguments['path']
    query = arguments['query']
    context_chars = arguments.get('context_chars', 100)
    
    if not os.path.exists(path): return ToolResult(isError=True, content=[TextContent(text="File not found.")])
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    
    # Simple regex search
    matches = []
    for m in re.finditer(query, content, re.IGNORECASE):
        start = max(0, m.start() - context_chars)
        end = min(len(content), m.end() + context_chars)
        matches.append({
            "match": m.group(0),
            "context": content[start:end].replace("\n", " "),
            "offset": m.start()
        })
        if len(matches) > 50: break # Cap results
        
    return dict_to_result({"path": path, "query": query, "matches": matches, "count": len(matches)}, "Search Results")

async def search_local_library(arguments: dict) -> ToolResult:
    """
    Search ENTIRE local library for a keyword.
    Warning: Iterate all files.
    """
    query = arguments['query']
    ticker = arguments.get('ticker') # Optional filter
    
    base_dir = os.path.join(SecCore.get_downloader().download_folder, "sec-edgar-filings")
    if ticker: base_dir = os.path.join(base_dir, ticker)
    
    files = glob.glob(os.path.join(base_dir, "**", "*.txt"), recursive=True)
    
    results = []
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            if re.search(query, content, re.IGNORECASE):
                # Found
                results.append(f)
                if len(results) > 100: break
                
    return dict_to_result({"query": query, "found_files": results, "count": len(results)}, "Library Search")

async def calculate_readability_metrics(arguments: dict) -> ToolResult:
    """
    Calculate Gunning-Fog Index (Readability).
    Fog = 0.4 * ( (words/sentences) + 100 * (complex_words/words) )
    """
    path = arguments['path']
    if not os.path.exists(path): return ToolResult(isError=True, content=[TextContent(text="File not found.")])
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
    
    # Rough approximation
    # Remove HTML tags logic should be better (or reuse analysis cleaning)
    text = re.sub(r'<[^>]+>', ' ', text)
    sentences = re.split(r'[.!?]+', text)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    num_sentences = max(1, len(sentences))
    num_words = max(1, len(words))
    
    # Complex words: 3+ syllables. Rough heuristic: > 8 chars?
    # Better heuristic needed for "syllables" but length is a proxy for speed.
    complex_words = sum(1 for w in words if len(w) > 8) 
    
    asl = num_words / num_sentences
    phw = (complex_words / num_words) * 100
    fog = 0.4 * (asl + phw)
    
    return dict_to_result({
        "gunning_fog_index": fog,
        "interpretaton": "Grade Level" if fog < 12 else ("College" if fog < 16 else "Post-Grad/Obfuscated"),
        "metrics": {"avg_sentence_length": asl, "percent_complex_words": phw, "word_count": num_words}
    }, "Readability Metrics")
