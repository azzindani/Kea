"""
Task Context Pool - Shared data flow between research tasks.

This module provides a context pool that flows between tasks, enabling:
- URL chaining: Search results feed into crawlers
- Data persistence: DataFrames/tables passed between analysis steps
- Fact accumulation: Extracted facts available to subsequent tasks
- Code result storage: Python execution outputs accessible by other tasks
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TaskContextPool:
    """
    Shared context that flows between research tasks.
    
    Enables data chaining where output from task N becomes input for task N+1.
    
    Attributes:
        url_pool: URLs extracted from search results, available for crawlers
        data_pool: Named data objects (DataFrames, dicts) stored by tasks
        fact_pool: Extracted facts with source attribution
        code_results: Results from Python code execution
        tables_found: HTML tables extracted from web pages
    """
    
    # URL handling
    url_pool: list[str] = field(default_factory=list)
    crawled_urls: set[str] = field(default_factory=set)
    
    # Data storage
    data_pool: dict[str, Any] = field(default_factory=dict)
    tables_found: list[dict] = field(default_factory=list)
    
    # Facts and results
    fact_pool: list[dict] = field(default_factory=list)
    code_results: dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    urls_extracted: int = 0
    tables_extracted: int = 0
    
    def add_urls(self, urls: list[str]) -> int:
        """
        Add URLs to the pool, deduplicating and filtering.
        
        Args:
            urls: List of URLs to add
            
        Returns:
            Number of new URLs added
        """
        added = 0
        for url in urls:
            # Clean URL
            url = url.strip().rstrip('.,;:')
            
            # Skip if already in pool or already crawled
            if url in self.url_pool or url in self.crawled_urls:
                continue
            
            # Skip very short or broken URLs
            if len(url) < 20:
                continue
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.jpg', '.png', '.gif', '.zip']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                continue
            
            self.url_pool.append(url)
            added += 1
        
        self.urls_extracted += added
        if added > 0:
            logger.info(f"   🔗 Added {added} URLs to pool (total: {len(self.url_pool)})")
        
        return added
    
    def get_url(self) -> str | None:
        """
        Get next URL from pool and mark as crawled.
        
        Returns:
            URL string or None if pool is empty
        """
        if not self.url_pool:
            return None
        
        url = self.url_pool.pop(0)
        self.crawled_urls.add(url)
        return url
    
    def get_urls(self, count: int = 10) -> list[str]:
        """
        Get multiple URLs from pool.
        
        Args:
            count: Maximum number of URLs to return
            
        Returns:
            List of URLs
        """
        urls = []
        for _ in range(min(count, len(self.url_pool))):
            url = self.get_url()
            if url:
                urls.append(url)
        return urls
    
    def store_data(self, key: str, data: Any, description: str = "") -> None:
        """
        Store named data object for later use.
        
        Args:
            key: Unique identifier for the data
            data: The data object (DataFrame, dict, list, etc.)
            description: Human-readable description
        """
        self.data_pool[key] = {
            "data": data,
            "description": description,
            "type": type(data).__name__,
        }
        logger.info(f"   📊 Stored data '{key}': {type(data).__name__}")
    
    def get_data(self, key: str) -> Any:
        """Get stored data by key."""
        if key in self.data_pool:
            return self.data_pool[key]["data"]
        return None
    
    def list_data_keys(self) -> list[str]:
        """Get list of stored data keys."""
        return list(self.data_pool.keys())
    
    def add_table(self, table_data: dict, source_url: str = "") -> None:
        """
        Add extracted HTML table to pool.
        
        Args:
            table_data: Table as dict or DataFrame
            source_url: URL where table was found
        """
        self.tables_found.append({
            "data": table_data,
            "source": source_url,
        })
        self.tables_extracted += 1
    
    def add_fact(self, text: str, source: str, task_id: str = "") -> None:
        """Add extracted fact to pool."""
        self.fact_pool.append({
            "text": text[:2000],
            "source": source,
            "task_id": task_id,
        })
    
    def store_code_result(self, task_id: str, result: Any) -> None:
        """Store Python code execution result."""
        self.code_results[task_id] = result
        logger.info(f"   📋 Code result stored for '{task_id}'")
    
    def get_code_result(self, task_id: str) -> Any:
        """Get stored code execution result."""
        return self.code_results.get(task_id)
    
    def extract_urls_from_text(self, text: str) -> list[str]:
        """
        Extract URLs from text using multiple patterns.
        
        Args:
            text: Text to extract URLs from
            
        Returns:
            List of extracted URLs
        """
        urls = []
        
        # Pattern 1: URLs in parentheses (markdown links)
        urls.extend(re.findall(r'\((https?://[^\)\s]+)\)', text))
        
        # Pattern 2: URLs in brackets [url]
        urls.extend(re.findall(r'\[(https?://[^\]\s]+)\]', text))
        
        # Pattern 3: URLs after colon/space
        urls.extend(re.findall(r':\s*(https?://[^\s\)\]<>"]+)', text))
        
        # Pattern 4: Standalone URLs
        urls.extend(re.findall(r'(?<![(\[:])(https?://[^\s\)\]<>"]+)', text))
        
        # Deduplicate and clean
        unique_urls = list(set(urls))
        
        # Add to pool and return
        self.add_urls(unique_urls)
        
        return unique_urls
    
    def get_context_summary(self) -> str:
        """Get summary of current context for LLM prompts."""
        return f"""
Context Summary:
- URLs in pool: {len(self.url_pool)}
- URLs crawled: {len(self.crawled_urls)}
- Data stored: {self.list_data_keys()}
- Tables found: {len(self.tables_found)}
- Facts collected: {len(self.fact_pool)}
- Code results: {list(self.code_results.keys())}
"""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for state persistence."""
        return {
            "url_pool": self.url_pool,
            "crawled_urls": list(self.crawled_urls),
            "data_keys": self.list_data_keys(),
            "tables_count": len(self.tables_found),
            "facts_count": len(self.fact_pool),
            "urls_extracted": self.urls_extracted,
        }


# Global context pool instance
_context_pool: TaskContextPool | None = None


def get_context_pool() -> TaskContextPool:
    """Get or create global context pool."""
    global _context_pool
    if _context_pool is None:
        _context_pool = TaskContextPool()
    return _context_pool


def reset_context_pool() -> TaskContextPool:
    """Reset context pool for new research session."""
    global _context_pool
    _context_pool = TaskContextPool()
    return _context_pool
