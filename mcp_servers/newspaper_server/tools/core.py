
import warnings

# Suppress "invalid escape sequence" warnings from newspaper3k
warnings.filterwarnings("ignore", category=SyntaxWarning, module="newspaper")

from typing import Optional, List, Dict, Any
import newspaper
from newspaper import Article, Source
import nltk

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class NewsClient:
    """
    Wrapper for newspaper3k to handle configuration and caching.
    """
    
    @staticmethod
    def get_config() -> newspaper.Config:
        config = newspaper.Config()
        # Use a specific user agent to avoid being blocked or served mobile versions that break parsing
        # Updated to Chrome 120 (late 2023)
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config.request_timeout = 30 # Increased timeout for slow sites
        config.number_threads = 3 # Reduce threads to avoid rate limiting
        return config

    @staticmethod
    def get_article(url: str, params: dict) -> Article:
        """
        Download and parse an article.
        """
        config = NewsClient.get_config()
        
        # Override language if needed
        lang = params.get('language', 'en')
        config.language = lang
        config.memoize_articles = params.get('memoize', True)
        
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        # Optional NLP
        if params.get('nlp', False):
            article.nlp()
            
        return article

    @staticmethod
    def build_source(url: str, memoize: bool = True) -> Source:
        """
        Build a news Source object (scanning/discovery).
        """
        config = NewsClient.get_config()
        config.memoize_articles = memoize
        
        # newspaper.build is heavy, it invokes multi-threading by default
        source = newspaper.build(url, config=config)
        return source

def dict_to_result(data: Any, title: str = "Result") -> Any:
    """Helper for MCP consistency"""
    from shared.mcp.protocol import ToolResult, TextContent
    import json
    
    # Handle non-serializable objects if any
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(data, indent=2, default=str))]
    )
