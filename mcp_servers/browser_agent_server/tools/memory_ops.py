import hashlib
import asyncio
from typing import Dict, Any, List

# In-memory search memory (would be persisted to HuggingFace in production)
SEARCH_MEMORY: Dict[str, dict] = {}

async def search_memory_add(query: str, url: str, title: str = "", summary: str = "", relevance_score: float = 0.5, credibility_score: float = 0.5) -> str:
    """Add a search result to memory for future reference."""
    # Create memory key
    key = hashlib.md5(url.encode()).hexdigest()[:12]
    
    entry = {
        "query": query,
        "url": url,
        "title": title,
        "summary": summary,
        "relevance": relevance_score,
        "credibility": credibility_score,
        "timestamp": asyncio.get_event_loop().time(),
    }
    
    SEARCH_MEMORY[key] = entry
    
    result = f"# 🧠 Memory Updated\n\n"
    result += f"**Key**: {key}\n"
    result += f"**URL**: {url}\n"
    result += f"**Query**: {query}\n"
    result += f"**Relevance**: {relevance_score:.2f}\n"
    result += f"**Credibility**: {credibility_score:.2f}\n\n"
    result += f"Total memories: {len(SEARCH_MEMORY)}\n"
    
    return result

async def search_memory_recall(query: str, min_relevance: float = 0.0) -> str:
    """Recall previous search results from memory."""
    query_lower = query.lower()
    
    result = f"# 🧠 Memory Recall\n\n"
    result += f"**Query**: {query}\n"
    result += f"**Min Relevance**: {min_relevance}\n\n"
    
    matches = []
    for key, entry in SEARCH_MEMORY.items():
        # Simple text matching
        if (query_lower in entry.get("query", "").lower() or 
            query_lower in entry.get("title", "").lower() or
            query_lower in entry.get("summary", "").lower()):
            if entry.get("relevance", 0) >= min_relevance:
                matches.append((key, entry))
    
    result += f"## Found {len(matches)} Memories\n\n"
    
    for key, entry in matches:
        result += f"### {entry.get('title', 'No title')}\n"
        result += f"- **URL**: {entry.get('url')}\n"
        result += f"- **Original Query**: {entry.get('query')}\n"
        result += f"- **Relevance**: {entry.get('relevance', 0):.2f}\n"
        result += f"- **Credibility**: {entry.get('credibility', 0):.2f}\n\n"
    
    return result
