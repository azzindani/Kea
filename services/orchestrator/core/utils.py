"""
Orchestrator Core Utilities.

Shared helper functions for graph nodes and agents.
"""

from __future__ import annotations

import re
from typing import Any

from shared.logging import get_logger
from shared.context_pool import get_context_pool
from services.orchestrator.agents.code_generator import generate_fallback_code

logger = get_logger(__name__)


def extract_url_from_text(text: str) -> str | None:
    """Extract first URL from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None


def extract_entity_from_desc(text: str) -> str:
    """Extract entity/company name from description."""
    # Remove common prefixes and extract the main subject
    text = text.strip()
    # Try to find quoted entities
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
    if quoted:
        return quoted[0][0] or quoted[0][1]
    # Otherwise use the whole description as query
    return text[:200]


def build_tool_inputs(tool_name: str, description: str, original_inputs: dict, collected_facts: list = None) -> dict:
    """
    Build proper inputs based on tool requirements.
    
    Centralized logic for mapping research tasks to tool arguments.
    Handles URL chaining from context pool and smart fallback.
    """
    ctx = get_context_pool()
    
    # PYTHON TOOLS
    if tool_name in ["run_python", "execute_code", "parse_document"]:
        if "code" in original_inputs: return original_inputs
        code = generate_fallback_code(description, collected_facts or [])
        return {"code": code}
    
    if tool_name in ["sql_query", "analyze_data"]:
            # TRANSFORM: Smart Logic -> Python Code
            if "code" in original_inputs: return original_inputs
            code = generate_fallback_code(description, collected_facts or [])
            return {"code": code}
    
    # DATAFRAME OPS - needs operation parameter
    if tool_name == "dataframe_ops":
        if "operation" in original_inputs: return original_inputs
        # Map description to operation
        desc_lower = description.lower()
        if "filter" in desc_lower:
            return {"operation": "filter", "query": description}
        elif "sort" in desc_lower:
            return {"operation": "sort", "column": "value", "ascending": False}
        elif "group" in desc_lower:
            return {"operation": "groupby", "columns": ["category"]}
        elif "merge" in desc_lower:
            return {"operation": "merge"}
        else:
            # Default to filter with description as query
            return {"operation": "filter", "query": description}
    
    # SCRAPING & CRAWLING
    if tool_name in ["scrape_url", "fetch_url", "link_extractor", "sitemap_parser"]:
        if "url" in original_inputs: return original_inputs
        
        # Try to extract URL from description
        url_from_desc = extract_url_from_text(description)
        if url_from_desc:
            return {"url": url_from_desc}
        
        # ORCHESTRATION FIX: Auto-chain URLs from context pool
        # If no URL provided, pull one from the pool of discovered URLs
        next_url = ctx.get_url()
        if next_url:
            logger.info(f"   🔗 Chained URL from pool to {tool_name}: {next_url}")
            return {"url": next_url}
            
        return None
    
    # BROWSER SCRAPE - needs URL
    if tool_name in ["browser_scrape", "safe_download", "page_screenshot"]:
        if "url" in original_inputs: return original_inputs
        
        url_from_desc = extract_url_from_text(description)
        if url_from_desc:
            return {"url": url_from_desc}
        
        next_url = ctx.get_url()
        if next_url:
            logger.info(f"   🔗 Chained URL from pool to {tool_name}: {next_url}")
            return {"url": next_url}
        return None
    
    if tool_name == "web_crawler":
        if "start_url" in original_inputs: return original_inputs
        url_from_desc = extract_url_from_text(description)
        if url_from_desc:
            return {"start_url": url_from_desc, "max_depth": 3, "max_pages": 50}
        crawl_url = ctx.get_url()
        if crawl_url: return {"start_url": crawl_url, "max_depth": 3, "max_pages": 50}
        return None

    # BROWSER TOOLS
    if tool_name in ["human_search", "human_like_search"]:
        if "query" in original_inputs: return {"query": original_inputs["query"], "max_sites": 10}
        return {"query": description, "max_sites": 10}
        
    if tool_name == "source_validator":
        if "url" in original_inputs: return original_inputs
        next_url = ctx.get_url()
        if next_url: return {"url": next_url}
        return None
        
    if tool_name == "multi_browse":
        if "urls" in original_inputs: return original_inputs
        return None
    
    # EDGAR / SEC TOOLS
    if tool_name in ["edgar_search", "sec_search"]:
        if "company" in original_inputs: return original_inputs
        # Extract company name from description
        entity = extract_entity_from_desc(description)
        return {"company": entity}
    
    if tool_name in ["edgar_filing_content", "sec_filing"]:
        if "accession_number" in original_inputs: return original_inputs
        # We need accession number from previous edgar_search results
        # Check collected facts for accession numbers
        if collected_facts:
            for fact in collected_facts:
                text = fact.get("text", "") if isinstance(fact, dict) else str(fact)
                acc_match = re.search(r'\d{10}-\d{2}-\d{6}', text)
                if acc_match:
                    return {"accession_number": acc_match.group(0)}
        return None
    
    # SENTIMENT / NLP TOOLS
    if tool_name in ["sentiment_analysis", "text_analysis", "summarize"]:
        if "text" in original_inputs: return original_inputs
        # Use collected facts as text source
        if collected_facts:
            texts = []
            for fact in collected_facts[:5]:
                text = fact.get("text", "") if isinstance(fact, dict) else str(fact)
                texts.append(text)
            combined = " ".join(texts)[:5000]
            if combined.strip():
                return {"text": combined}
        # Fallback to description
        return {"text": description}

    # SEARCH TOOLS (default)
    if tool_name in ["web_search", "news_search", "fetch_data"]:
        if "query" in original_inputs: return original_inputs
        return {"query": description, "max_results": 20}
    
    # DATA URL TOOLS (data_profiler, data_cleaner, feature_engineer, auto_ml)
    if tool_name in ["data_profiler", "data_cleaner", "feature_engineer", "auto_ml"]:
        if "data_url" in original_inputs: return original_inputs
        
        # Try to extract URL from description
        url_from_desc = extract_url_from_text(description)
        if url_from_desc:
            return {"data_url": url_from_desc}
        
        # Try to get URL from context pool
        next_url = ctx.get_url()
        if next_url:
            logger.info(f"   🔗 Chained data_url from pool to {tool_name}: {next_url}")
            return {"data_url": next_url}
        
        # Fallback: Use description as a hint (may not work but avoids hard failure)
        return {"data_url": f"data://{description[:100]}"}
    
    # TEXT CODING TOOL
    if tool_name == "text_coding":
        if "text" in original_inputs: return original_inputs
        # Use collected facts as text source
        if collected_facts:
            texts = []
            for fact in collected_facts[:10]:
                text = fact.get("text", "") if isinstance(fact, dict) else str(fact)
                texts.append(text)
            combined = " ".join(texts)[:10000]
            if combined.strip():
                return {"text": combined}
        return {"text": description}
    
    # THEME EXTRACTOR - needs 'texts' (list)
    if tool_name == "theme_extractor":
        if "texts" in original_inputs: return original_inputs
        if collected_facts:
            texts_list = []
            for fact in collected_facts[:20]:
                text = fact.get("text", "") if isinstance(fact, dict) else str(fact)
                if text.strip():
                    texts_list.append(text[:2000])
            if texts_list:
                return {"texts": texts_list}
        return {"texts": [description]}
    
    # TRIANGULATION CHECK - needs 'claim'
    if tool_name == "triangulation_check":
        if "claim" in original_inputs: return original_inputs
        # Use description as the claim to verify
        return {"claim": description}
    
    # INVESTIGATION GRAPH - needs 'entity_type'
    if tool_name == "investigation_graph_add":
        if "entity_type" in original_inputs: return original_inputs
        
        # Try to detect entity type from description
        desc_lower = description.lower()
        entity_type = "UNKNOWN"
        entity_name = extract_entity_from_desc(description)
        
        if any(word in desc_lower for word in ["company", "corp", "inc", "ltd", "business"]):
            entity_type = "COMPANY"
        elif any(word in desc_lower for word in ["person", "ceo", "founder", "director", "employee"]):
            entity_type = "PERSON"
        elif any(word in desc_lower for word in ["document", "filing", "report", "article"]):
            entity_type = "DOCUMENT"
        elif any(word in desc_lower for word in ["event", "meeting", "transaction", "deal"]):
            entity_type = "EVENT"
        
        return {"entity_type": entity_type, "entity_name": entity_name}
        
    return original_inputs
