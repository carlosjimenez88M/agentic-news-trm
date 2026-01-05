"""Abstract base scraper for data collection."""

from abc import ABC, abstractmethod
from typing import Any, List
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, timeout: int = 30):
        """Initialize scraper.

        Args:
            timeout: Timeout in seconds for requests
        """
        self.timeout = timeout
        self.logger = logger

    @abstractmethod
    def scrape(self, **kwargs) -> List[Any]:
        """Scrape data from source.

        Returns:
            List of scraped data objects
        """
        pass

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.__class__.__name__}] {message}")

    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"[{self.__class__.__name__}] {message}")

    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(f"[{self.__class__.__name__}] {message}")


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass
