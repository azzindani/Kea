import uuid
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
import structlog
import os

logger = structlog.get_logger()

class SoupManager:
    """
    Singleton to manage multiple BeautifulSoup objects in memory.
    Allows stateful interaction with parsed HTML across multiple tool calls.
    """
    _soups: Dict[str, BeautifulSoup] = {}
    _active_id: Optional[str] = None

    @classmethod
    def load_html(cls, html_content: str, parser: str = "lxml") -> str:
        """Parse HTML and store it. Returns Soup ID."""
        soup_id = str(uuid.uuid4())
        try:
            soup = BeautifulSoup(html_content, parser)
            cls._soups[soup_id] = soup
            cls._active_id = soup_id
            logger.info("soup_loaded", id=soup_id, parser=parser)
            return soup_id
        except Exception as e:
            # Fallback to html.parser if lxml fails or isn't installed
            if parser == "lxml":
                logger.warning("lxml_failed_fallback_html_parser", error=str(e))
                return cls.load_html(html_content, "html.parser")
            raise e

    @classmethod
    def load_file(cls, file_path: str, parser: str = "lxml") -> str:
        """Read file and parse."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            return cls.load_html(f.read(), parser)

    @classmethod
    def get_soup(cls, soup_id: Optional[str] = None) -> BeautifulSoup:
        """Get soup instance. Defaults to last active."""
        target_id = soup_id or cls._active_id
        if not target_id or target_id not in cls._soups:
            raise ValueError("No active soup. Parse HTML first.")
        return cls._soups[target_id]

    @classmethod
    def list_soups(cls) -> Dict[str, str]:
        """List active soup IDs and basic info."""
        return {
            sid: f"Tags: {len(soup.find_all())}, Text: {len(soup.text)[:50]}..." 
            for sid, soup in cls._soups.items()
        }

    @classmethod
    def close_soup(cls, soup_id: str) -> str:
        """Remove from memory."""
        if soup_id in cls._soups:
            del cls._soups[soup_id]
            if cls._active_id == soup_id:
                cls._active_id = list(cls._soups.keys())[-1] if cls._soups else None
            return f"Closed {soup_id}"
        return "Soup ID not found"
